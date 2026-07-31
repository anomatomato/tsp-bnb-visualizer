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
from .data_schema import TSPGraph, TSPInstance
from .relaxed_solution import RelaxedSolution


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

    def outgoing_edges(self, vertices: list[int]):
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


class LPRelaxationSolver(Relaxation):
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
        logger: logging.Logger | None = None,
    ):
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.logger.info("Creating model ...")
        self.logger.info(
            f"Graph has {instance.graph.number_of_nodes()} nodes and {instance.graph.number_of_edges()} edges"
        )

        self.instance = instance
        self.graph = instance.graph
        self.edge_fixations = fixations

        self.model = highspy.Highs()
        # self.model.silent()

        self._vars = _EdgeVariables(instance.graph, self.model)
        self._weights: dict[tuple[int, int], float] = {
            (u, v): weight for u, v, weight in self.graph.edges.data("weight")
        }

        self._add_objective()
        self._add_constraints()
        self._apply_fixations()

    def _add_constraints(self) -> None:
        # Degree constraints:
        # Every node has two incident edges.
        for v in self.graph.nodes:
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
        edges = list(self.graph.edges)
        for edge_idx, val in self.edge_fixations.fixed_edges():
            edge: tuple[int, int] = edges[edge_idx]
            u, v = edge
            var = self._vars.x(u, v)

            self.model.changeColBounds(col=var, lower_bound=val, upper_bound=val)

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

    def _find_subtours(self, tol: float = 0.01) -> list[list[int]]:
        """Find subtours in the graph"""
        solution_graph = self._vars.as_graph(threshold=tol)

        # Find disconnected subgraphs
        if not nx.is_connected(solution_graph):
            # pyrefly: ignore
            return [list(c) for c in nx.connected_components(solution_graph)]
        # Find minimum cut separation (for fractional edges)
        cut_value, (S, T) = nx.stoer_wagner(solution_graph, weight="x")
        if cut_value < 2 - tol:
            return [S]
        return []

    def _add_subtour_cuts(self, subtours: list[list[int]]) -> None:
        """Add subtour elimination cuts: sum(x_{ij} for i in S, j not in S) >= 2"""
        if len(subtours) > 1:
            for subtour in subtours:
                outgoing_edge_sum = self.model.qsum(
                    x for _, x in self._vars.outgoing_edges(subtour)
                )
                self.model.addConstr(
                    outgoing_edge_sum >= 2, name=f"sec_{'-'.join(map(str, subtour))}"
                )

    def solve(self, max_cuts: int = 100) -> RelaxedSolution:
        """Solve the LP with lazy subtour elimination constraints and return the resulting relaxation."""
        self.logger.info("Solving model ...")

        for _ in range(max_cuts):
            self.model.run()

            # Find subtours in current fractional solution
            subtours = self._find_subtours(tol=0.001)

            if len(subtours) < 2:
                break  # no cuts to add

            # Add cuts for all subtours
            self._add_subtour_cuts(subtours)

        self._log_solve_status()
        # solution = self.model.getSolution()
        # basis = self.model.getBasis()
        # info = self.model.getInfo()
        status = self.model.getModelStatus()

        if status == HighsModelStatus.kInfeasible:
            return RelaxedSolution.create_infeasible(self.instance)

        if status != HighsModelStatus.kOptimal:
            raise RuntimeError(
                f"HiGHs LP model terminated with unknown solution status: {self.model.modelStatusToString(status)}"
            )

        edge_fractions = self.model.allVariableValues()
        objective_val = self.model.getObjectiveValue()

        return RelaxedSolution(
            instance=self.instance,
            edge_fractions=edge_fractions,
            lower_bound=objective_val,
        )


MyRelaxationSolver = LPRelaxationSolver  # type: ignore[assignment]
