"""
LP Relaxation Solver for TSP Branch-and-Bound.

Builds a HiGHS LP model for the fractional TSP at a given BnB node, applies
the branch fixations, and iteratively adds subtour elimination constraints
until the LP solution contains no violated subtour or a cut limit is reached.

The LP objective is a **lower bound** on the best integer tour consistent
with the given fixations. If this bound exceeds the current best-known tour
cost, the BnB node can be pruned.
"""

import abc
import logging

import highspy
import networkx as nx
from highspy import HighsModelStatus, HighsVarType

from .branching_decisions import BranchingDecisions
from .cut_pool import CutPool
from .data_schema import TSPGraph, TSPInstance
from .relaxed_solution import RelaxedSolution, SolveStatus


class Relaxation(abc.ABC):
    """
    Abstract base for relaxation strategies.

    Implement `solve` to compute a **lower bound** on the best 0/1 TSP tour
    consistent with the given fixations. The bound can be used by the BnB
    search to prune nodes whose bound exceeds the best-known tour cost.
    """

    def __init__(self, instance: TSPInstance, fixations: BranchingDecisions): ...
    @abc.abstractmethod
    def solve(self) -> RelaxedSolution:
        """
        Return a `RelaxedSolution` satisfying:
          - fixed edges in `decisions` remain at 0 or 1;
          - lower_bound <= best feasible 0/1 solution under those decisions.
        """
        ...


class _EdgeVariables:
    def __init__(self, G: TSPGraph, model: highspy.Highs):
        self._graph = G
        self._model = model
        self._vars = {
            (u, v): model.addVariable(
                type=HighsVarType.kContinuous, lb=0.0, ub=1.0, name=f"edge_{u}_{v}"
            )
            for u, v in G.edges
        }

    def __iter__(self):
        return iter(self._vars.items())

    def x(self, u: int, v: int) -> highspy.highs_var:
        """Return the variable handle for edge (u, v) — works in either order."""
        if (u, v) in self._vars:
            return self._vars[u, v]
        return self._vars[v, u]

    def crossing_edges(self, vertices: set[int] | frozenset[int]):
        """Yield ((u, v), var) for every edge with exactly one endpoint in `vertices`."""
        for (u, v), x in self._vars.items():
            if u in vertices and v not in vertices:
                yield (u, v), x
            elif v in vertices and u not in vertices:
                yield (v, u), x

    def incident_edges(self, v: int):
        """Yield ((u,v), var) for every edge incident to v."""
        for n in self._graph.neighbors(v):
            yield (v, n), self.x(v, n)

    def all_values(self) -> dict[tuple[int, int], float]:
        """Bulk-extract all variable values from current solution."""
        values = self._model.allVariableValues()
        return dict(zip(self._vars.keys(), values))

    def as_graph(self, threshold: float = 0.001) -> nx.Graph[int]:
        """Return the current LP solution as a graph (edges with x > threshold)."""
        graph = nx.Graph()
        graph.add_nodes_from(self._graph.nodes)
        for (u, v), val in self.all_values().items():
            if val > threshold:
                graph.add_edge(
                    u,
                    v,
                    x=val,
                )
        return graph


class LPRelaxation(Relaxation):
    """
    LP Relaxation Solver for TSP with branch fixations.

    Builds a HiGHS model from the TSP instance and current edge fixations,
    then solves the fractional LP. Iteratively adds subtour elimination cuts
    until the LP contains no violated subtour (or `max_cuts` is reached).
    Returns a `RelaxedSolution` with the edge fractions and the LP objective,
    which serves as a lower bound on the best integer tour under these fixations.
    """

    def __init__(
        self,
        instance: TSPInstance,
        fixations: BranchingDecisions,
        *,
        cut_pool: CutPool,
        parent_basis: highspy.HighsBasis | None = None,
        logger: logging.Logger | None = None,
    ):
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.logger.info("Creating model ...")
        self.logger.info(
            f"Graph has {instance.graph.number_of_nodes()} nodes and {instance.graph.number_of_edges()} edges"
        )

        self._instance = instance
        self._graph = instance.graph
        self._edge_fixations = fixations
        self._cut_pool = cut_pool
        self._parent_basis = parent_basis

        self.model = highspy.Highs()
        # self.model.silent()

        self._vars = _EdgeVariables(instance.graph, self.model)
        self._weights: dict[tuple[int, int], float] = {
            (u, v): weight for u, v, weight in self._graph.edges.data("weight")
        }

        self._add_objective()
        self._add_degree_constraints()
        self._add_pool_cuts_to_lp()
        self._apply_fixations()

    def _add_degree_constraints(self) -> None:
        # Degree constraints:
        # Every node has two incident edges.
        for v in self._graph.nodes:
            v_degree = self.model.qsum(x for _, x in self._vars.incident_edges(v))
            self.model.addConstr(
                v_degree == 2,
                name=f"degree_constr_{v}",
            )

    def _add_objective(self) -> None:
        tour_cost = self.model.qsum(self._weights[u, v] * x for (u, v), x in self._vars)
        self.model.minimize(tour_cost)

    def _apply_fixations(self) -> None:
        """Fix variable bounds according to the branching decisions"""
        edges = list(self._graph.edges)
        for edge_idx, val in self._edge_fixations.fixed_edges():
            edge: tuple[int, int] = edges[edge_idx]
            u, v = edge
            var = self._vars.x(u, v)

            self.model.changeColBounds(col=var, lower_bound=val, upper_bound=val)

    def _find_subtours(self, tol: float = 0.001) -> list[frozenset[int]]:
        """Return raw subtours. One per connected component, or the smaller side
        of a stoer-wagner min-cut if the solution graph is connected."""
        solution_graph = self._vars.as_graph(threshold=tol)

        # Find disconnected subgraphs
        if not nx.is_connected(solution_graph):
            # pyrefly: ignore
            return [frozenset(c) for c in nx.connected_components(solution_graph)]
        # Find minimum cut separation (for fractional edges)
        cut_value, (S, T) = nx.stoer_wagner(solution_graph, weight="x")
        if cut_value < 2 - tol:
            return [S if len(S) <= len(T) else T]
        return []

    def _add_subtour_cuts(self, subtours: list[frozenset[int]]) -> None:
        """
        Register subtour elimination cuts to the global pool AND the LP model: sum(x_{ij} for i in S, j not in S) >= 2
        Skips cuts that are already in the pool (they're already in the LP from `__init__`)
        """
        for raw_subtour in subtours:
            if raw_subtour in self._cut_pool:
                continue  # already in LP
            canonical = self._cut_pool.add(raw_subtour)
            if canonical is None:
                continue  # empty/full - not a valid cut
            self._add_sec_constraints(canonical)

    def _add_pool_cuts_to_lp(self) -> None:
        for canonical in self._cut_pool.all():
            self._add_sec_constraints(canonical)

    def _add_sec_constraints(self, canonical: frozenset[int]) -> None:
        """Add a single SEC: sum(x_ij for i in S, j not in S) >= 2."""
        crossing = self.model.qsum(x for _, x in self._vars.crossing_edges(canonical))
        self.model.addConstr(
            crossing >= 2,
            name=f"sec_{'-'.join(map(str, sorted(canonical)))}",
        )

    def _log_solve_status(self) -> None:
        info = self.model.getInfo()
        status = self.model.getModelStatus()

        self.logger.debug(f"Model status = {self.model.modelStatusToString(status)}")
        self.logger.debug("")
        self.logger.debug(f"Optimal objective ={info.objective_function_value}")
        self.logger.debug(f"Iteration count ={info.simplex_iteration_count}")
        self.logger.debug(
            f"Primal solution status ={
                (self.model.solutionStatusToString(info.primal_solution_status))
            }"
        )
        self.logger.debug(
            f"Dual solution status = {
                (self.model.solutionStatusToString(info.dual_solution_status))
            }"
        )
        self.logger.debug(
            f"Basis validity = {self.model.basisValidityToString(info.basis_validity)}"
        )

    def solve(self, max_cuts: int = 100) -> RelaxedSolution:
        """Solve the LP with lazy subtour elimination constraints and return the resulting relaxation."""
        if self._parent_basis is not None:
            try:
                self.model.setBasis(self._parent_basis)
            except Exception as e:
                self.logger.debug(f"setBasis failed (cold-start fallback): {e}")

        self.logger.info("Solving model ...")

        for _ in range(max_cuts):
            self.model.run()

            # Find subtours in current fractional solution
            subtours = self._find_subtours()

            if not subtours:
                break  # no cuts to add

            self._add_subtour_cuts(subtours)

        status = self.model.getModelStatus()
        if status == HighsModelStatus.kInfeasible:
            return RelaxedSolution.create_infeasible(self._instance)

        self._log_solve_status()
        # solution = self.model.getSolution()
        # info = self.model.getInfo()

        if status != HighsModelStatus.kOptimal:
            raise RuntimeError(
                f"HiGHs LP model terminated with unknown solution status: {self.model.modelStatusToString(status)}"
            )

        basis = self.model.getBasis()
        edge_fractions = tuple(x for _, x in self._vars.all_values())
        objective_val = self.model.getObjectiveValue()

        return RelaxedSolution(
            instance=self._instance,
            edge_fractions=edge_fractions,
            lower_bound=objective_val,
            status=SolveStatus.OPTIMAL,
            basis=basis,
        )


# MyRelaxationSolver = LPRelaxationSolver  # type: ignore[assignment]
