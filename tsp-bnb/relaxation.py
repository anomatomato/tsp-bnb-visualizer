"""
Relaxation Module

In branch-and-bound, a relaxation of the TSP yields a lower bound
on the best feasible solution within a branch. If this bound exceeds your
current best feasible solution, you can prune that branch and skip exploring it.

This file provides three example strategies:
  1. VeryNaiveRelaxationSolver:
     - Ignores capacity entirely, sets every unfixed item to 1.
     - Fastest, loosest bound.
  2. NaiveRelaxationSolver:
     - Checks that already-fixed items of 1 fit capacity.
     - Sets all unfixed items to 1, ignoring capacity beyond fixed part.
     - Slightly tighter bound than VeryNaive.
  3. MyRelaxationSolver:
     - Stub for your own algorithm (e.g., fractional knapsack, propagation).

You should subclass `RelaxationSolver` and implement `solve()`
so that:
  a) fixed decisions remain unchanged;
  b) objective <= best 0/1 solution consistent with those decisions.
"""

import abc
import logging
from collections.abc import Iterable

import highspy
import networkx as nx
from highspy import HighsVarType

from .branching_decisions import BranchingDecisions
from .data_schema import TSPGraph, TSPInstance
from .relaxed_solution import RelaxedSolution


class Relaxation(abc.ABC):
    """
    Abstract base for relaxation strategies.

    Implement `solve` to compute an upper bound on the best 0/1 solution
    consistent with given decisions.
    """

    def __init__(self, instance: TSPInstance, fixations: BranchingDecisions):
        self.instance = instance
        self.edge_fixations = fixations

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

    def x(self, v: int, w: int) -> highspy.highs_var:
        """Return the variable of the edge connecting `v` and `w`"""
        if (v, w) in self._vars:
            return self._vars[v, w]
        return self._vars[w, v]

    def outgoing_edges(self, vertices: Iterable[int]):
        for (v, w), x in self._vars.items():
            if v in vertices and w not in vertices:
                yield (v, w), x
            elif w in vertices and v not in vertices:
                yield (w, v), x

    def incident_edges(self, v: int):
        for n in self._graph.neighbors(v):
            yield (v, n), self.x(v, n)

    def as_graph(self, tol: float = 0.01):
        """
        Return the current solution as a graph.
        """
        graph: TSPGraph = nx.Graph()
        for (v, w), x in self:
            if tol < x.X:
                graph.add_edge(v, w, x=x.X)
        return graph


class LPRelaxationSolver(Relaxation):
    """
    LP Relaxation Solver for TSP.
    """

    def __init__(
        self,
        instance: TSPInstance,
        fixations: BranchingDecisions,
        logger: logging.Logger | None,
    ):
        if logger is None:
            logger = logging.getLogger(__name__)
        logger.info("Creating model ...")
        logger.info(
            f"Graph has {instance.graph.number_of_nodes()} nodes and {instance.graph.number_of_edges()} edges"
        )

        super().__init__(instance, fixations)
        self.model = highspy.Highs()
        self.graph = instance.graph

        self._vars = _EdgeVariables(instance.graph, self.model)

    def solve(self) -> RelaxedSolution:
        self.model.run()

        solution = self.model.getSolution()
        basis = self.model.getBasis()
        info = self.model.getInfo()
        model_status = self.model.getModelStatus()

        print("Model status = ", self.model.modelStatusToString(model_status))
        print()
        print("Optimal objective = ", info.objective_function_value)
        print("Iteration count = ", info.simplex_iteration_count)
        print(
            "Primal solution status = ",
            self.model.solutionStatusToString(info.primal_solution_status),
        )
        print(
            "Dual solution status = ",
            self.model.solutionStatusToString(info.dual_solution_status),
        )
        print(
            "Basis validity = ", self.model.basisValidityToString(info.basis_validity)
        )

        # TODO: Subtour elimination constraints and edge_fractions
        return RelaxedSolution(
            instance=self.instance,
            edge_fractions=[],
            lower_bound=info.objective_function_value,
        )


# class VeryNaiveRelaxationSolver(Relaxation):
#     """
#     A relaxation solver for the knapsack problem that naively sets every unfixed
#     item to 1 without considering the capacity constraint. This approach provides
#     a very loose upper bound for the problem.
#
#     Explanation:
#     The solver assumes that all unfixed items can be fully included in the knapsack
#     (i.e., their selection is set to 1.0) regardless of the capacity constraint.
#     This results in an overestimation of the objective value, making it an upper
#     bound. The rationale is that the true optimal solution cannot exceed this
#     value since it must respect the capacity constraint, which this naive approach
#     ignores.
#     """
#
#     def solve(
#         self, instance: TSPInstance, decisions: BranchingDecisions
#     ) -> RelaxedSolution:
#         # build selection: 1.0 for fixed 1 or unfixed, 0 for fixed 0
#         selection = [0.0 if x == 0 else 1.0 for x in decisions]
#         # compute objective value
#         upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
#         return RelaxedSolution(instance, selection, upper)


MyRelaxationSolver = LPRelaxationSolver  # type: ignore[assignment]


# class BasicRelaxationSolver(Relaxation):
#     """
#     Greedy fractional knapsack based on value/weight ratio.
#     """
#
#     def solve(
#         self, instance: TSPInstance, decisions: BranchingDecisions
#     ) -> RelaxedSolution:
#         # fix items, check feasibility
#         used = sum(item.weight for item, x in zip(instance.items, decisions) if x == 1)
#         if used > instance.capacity:
#             return RelaxedSolution.create_infeasible(instance)
#
#         selection = [1.0 if x == 1 else 0.0 for x in decisions]
#         remaining = instance.capacity - used
#         # sort unfixed by ratio
#         indices = [i for i, x in enumerate(decisions) if x is None]
#         indices.sort(
#             key=lambda i: instance.items[i].value / instance.items[i].weight,
#             reverse=True,
#         )
#         for i in indices:
#             w = instance.items[i].weight
#             if w <= remaining:
#                 selection[i] = 1.0
#                 remaining -= w
#             else:
#                 selection[i] = remaining / w
#                 break
#         upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
#         return RelaxedSolution(instance, selection, upper)
#
#
# class StrengthenedRelaxationSolver(Relaxation):
#     """
#     Fractional greedy plus propagation of heavy items.
#     """
#
#     def _propagate(
#         self, instance: TSPInstance, decisions: BranchingDecisions
#     ) -> BranchingDecisions:
#         fix = decisions.copy()
#         capacity = instance.capacity - sum(
#             item.weight for item, x in zip(instance.items, fix) if x == 1
#         )
#         for i, x in enumerate(fix):
#             if x is None and instance.items[i].weight > capacity:
#                 fix.fix(i, 0)
#         return fix
#
#     def solve(
#         self, instance: TSPInstance, decisions: BranchingDecisions
#     ) -> RelaxedSolution:
#         fix = self._propagate(instance, decisions)
#         used = sum(item.weight for item, x in zip(instance.items, fix) if x == 1)
#         if used > instance.capacity:
#             return RelaxedSolution.create_infeasible(instance)
#         selection = [1.0 if x == 1 else 0.0 for x in fix]
#         remaining = instance.capacity - used
#         indices = [i for i, x in enumerate(fix) if x is None]
#         indices.sort(
#             key=lambda i: instance.items[i].value / instance.items[i].weight,
#             reverse=True,
#         )
#         for i in indices:
#             w = instance.items[i].weight
#             if w <= remaining:
#                 selection[i] = 1.0
#                 remaining -= w
#             else:
#                 selection[i] = remaining / w
#                 break
#         upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
#         return RelaxedSolution(instance, selection, upper)
#
#
