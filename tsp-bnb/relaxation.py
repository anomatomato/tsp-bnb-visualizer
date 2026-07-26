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

You should subclass `RelaxationSolver` and implement `solve(instance, decisions)`
so that:
  a) fixed decisions remain unchanged;
  b) objective <= best 0/1 solution consistent with those decisions.
"""

import abc

from .branching_decisions import BranchingDecisions
from .data_schema import TSPInstance
from .relaxed_solution import RelaxedSolution


class Relaxation(abc.ABC):
    """
    Abstract base for relaxation strategies.

    Implement `solve` to compute an upper bound on the best 0/1 solution
    consistent with given decisions.
    """

    @abc.abstractmethod
    def solve(
        self, instance: TSPInstance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        """
        Return a `RelaxedSolution` satisfying:
          - fixed edges in `decisions` remain at 0 or 1;
          - lower_bound <= best feasible 0/1 solution under those decisions.
        """
        ...


class VeryNaiveRelaxationSolver(Relaxation):
    """
    A relaxation solver for the knapsack problem that naively sets every unfixed
    item to 1 without considering the capacity constraint. This approach provides
    a very loose upper bound for the problem.

    Explanation:
    The solver assumes that all unfixed items can be fully included in the knapsack
    (i.e., their selection is set to 1.0) regardless of the capacity constraint.
    This results in an overestimation of the objective value, making it an upper
    bound. The rationale is that the true optimal solution cannot exceed this
    value since it must respect the capacity constraint, which this naive approach
    ignores.
    """

    def solve(
        self, instance: TSPInstance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        # build selection: 1.0 for fixed 1 or unfixed, 0 for fixed 0
        selection = [0.0 if x == 0 else 1.0 for x in decisions]
        # compute objective value
        upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
        return RelaxedSolution(instance, selection, upper)


class NaiveRelaxationSolver(Relaxation):
    """
    Ensure fixed 1's fit capacity; set every unfixed item to 1.
    """

    def solve(
        self, instance: TSPInstance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        # compute capacity after fixed 1 items
        used = sum(item.weight for item, x in zip(instance.items, decisions) if x == 1)
        if used > instance.capacity:
            return RelaxedSolution.create_infeasible(instance)

        selection = [0.0 if x == 0 else 1.0 for x in decisions]
        upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
        return RelaxedSolution(instance, selection, upper)


class MyRelaxationSolver(Relaxation):
    """
    Your relaxation solver stub.

    Implement any relaxation (e.g., fractional knapsack, propagation) to tighten bounds.
    """

    def solve(
        self, instance: TSPInstance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        # placeholder: behave like NaiveRelaxationSolver
        used = sum(item.weight for item, x in zip(instance.items, decisions) if x == 1)
        if used > instance.capacity:
            return RelaxedSolution.create_infeasible(instance)
        selection = [0.0 if x == 0 else 1.0 for x in decisions]
        upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
        return RelaxedSolution(instance, selection, upper)


# <Solution>


class BasicRelaxationSolver(Relaxation):
    """
    Greedy fractional knapsack based on value/weight ratio.
    """

    def solve(
        self, instance: TSPInstance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        # fix items, check feasibility
        used = sum(item.weight for item, x in zip(instance.items, decisions) if x == 1)
        if used > instance.capacity:
            return RelaxedSolution.create_infeasible(instance)

        selection = [1.0 if x == 1 else 0.0 for x in decisions]
        remaining = instance.capacity - used
        # sort unfixed by ratio
        indices = [i for i, x in enumerate(decisions) if x is None]
        indices.sort(
            key=lambda i: instance.items[i].value / instance.items[i].weight,
            reverse=True,
        )
        for i in indices:
            w = instance.items[i].weight
            if w <= remaining:
                selection[i] = 1.0
                remaining -= w
            else:
                selection[i] = remaining / w
                break
        upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
        return RelaxedSolution(instance, selection, upper)


class StrengthenedRelaxationSolver(Relaxation):
    """
    Fractional greedy plus propagation of heavy items.
    """

    def _propagate(
        self, instance: TSPInstance, decisions: BranchingDecisions
    ) -> BranchingDecisions:
        fix = decisions.copy()
        capacity = instance.capacity - sum(
            item.weight for item, x in zip(instance.items, fix) if x == 1
        )
        for i, x in enumerate(fix):
            if x is None and instance.items[i].weight > capacity:
                fix.fix(i, 0)
        return fix

    def solve(
        self, instance: TSPInstance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        fix = self._propagate(instance, decisions)
        used = sum(item.weight for item, x in zip(instance.items, fix) if x == 1)
        if used > instance.capacity:
            return RelaxedSolution.create_infeasible(instance)
        selection = [1.0 if x == 1 else 0.0 for x in fix]
        remaining = instance.capacity - used
        indices = [i for i, x in enumerate(fix) if x is None]
        indices.sort(
            key=lambda i: instance.items[i].value / instance.items[i].weight,
            reverse=True,
        )
        for i in indices:
            w = instance.items[i].weight
            if w <= remaining:
                selection[i] = 1.0
                remaining -= w
            else:
                selection[i] = remaining / w
                break
        upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
        return RelaxedSolution(instance, selection, upper)


MyRelaxationSolver = StrengthenedRelaxationSolver  # type: ignore[assignment]  # noqa: F811
# </Solution>
