"""
Heuristics Module

In branch-and-bound, a relaxation gives an upper bound on the best objective in a branch.
To tighten pruning, you need feasible (integral) solutions to serve as lower bounds.
Instead of waiting for an integral node, you can derive feasible solutions from the relaxation
(e.g., rounding, greedy inclusion) to improve search efficiency.

You can implement heuristics by subclassing `Heuristics` and overriding `search(instance, node)`.
`search` should yield zero or more feasible `RelaxedSolution` objects.
"""

import math
from abc import ABC, abstractmethod

from .data_schema import TSPInstance
from .relaxed_solution import RelaxedSolution


class HeuristicSolution(RelaxedSolution):
    """
    A feasible heuristic solution.
    Inherits from `RelaxedSolution` for compatibility with the rest of the codebase.
    """

    def copy(self) -> "HeuristicSolution":
        """
        Return a deep copy of this heuristic solution.
        """
        return HeuristicSolution(
            self.instance,
            list(self.edge_fractions),
            self.upper_bound,
        )


class Heuristics(ABC):
    """
    Abstract base for heuristic generators.

    Implement `search` to produce feasible solutions from a node's relaxed solution.
    """

    @abstractmethod
    def search(
        self, instance: TSPInstance, relaxed: RelaxedSolution
    ) -> tuple[HeuristicSolution, ...]:
        """
        Return a tuple of feasible `HeuristicSolution` objects for pruning.
        """
        ...


class MyHeuristic(Heuristics):
    """
    Your heuristic implementation.

    The simplest heuristic returns the node's relaxed solution
    if it is already feasible (integral and within capacity).
    """

    def search(
        self, instance: TSPInstance, relaxed: RelaxedSolution
    ) -> tuple[HeuristicSolution, ...]:
        if relaxed.has_valid_fractions() and relaxed.is_integral():
            heuristic_sol = HeuristicSolution(
                instance, relaxed.edge_fractions, relaxed.upper_bound
            )
            return (heuristic_sol,)
        return ()


# <Solution>


class RoundingDownHeuristic(Heuristics):
    """
    Heuristic that rounds down each fractional decision to 0 and yields the result
    if it fits within capacity.
    """

    def search(
        self, instance: TSPInstance, relaxed: RelaxedSolution
    ) -> tuple[HeuristicSolution, ...]:
        selection = [math.floor(x) for x in relaxed.edge_fractions]
        # compute objective value by summing selected items' values
        total_value = sum(
            item.value * sel for item, sel in zip(instance.items, selection)
        )
        sol = HeuristicSolution(instance, selection, total_value)
        if sol.has_valid_fractions():
            return (sol,)
        return ()


MyHeuristic = RoundingDownHeuristic  # type: ignore[assignment]  # noqa: F811
# </Solution>
