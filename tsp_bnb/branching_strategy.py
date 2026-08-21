"""
Branching Strategy Module

Defines how to split (branch) a BnB tree node when its current relaxed solution
is not yet a feasible integer solution. At each branching step:
 1. Select a decision variable that has not been fixed.
 2. Create two children by fixing that variable to 0 (exclude) and 1 (include).
 3. If all variables are fixed, no branches are returned (leaf node).

You should implement your own strategies by subclassing `BranchingStrategy`.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .bnb_nodes import BnBNode, BranchingDecisions


class BranchingStrategy(ABC):
    """
    Abstract base for branching policies based on a node's relaxed solution.

    Subclasses must implement `make_branching_decisions` to return zero,
    two, or more `BranchingDecisions` objects describing child nodes.
    """

    @abstractmethod
    def make_branching_decisions(self, node: BnBNode) -> Iterable[BranchingDecisions]:
        """
        Return an iterable of `BranchingDecisions` to create child nodes.
        If no decisions can be made (all variables fixed), return an empty iterable.
        """
        ...


class FirstUndecidedBranchingStrategy(BranchingStrategy):
    """
    Branch on the first variable that has not yet been fixed.
    """

    def make_branching_decisions(self, node: BnBNode) -> tuple[BranchingDecisions, ...]:
        # find the smallest index i where no decision has been made
        first_unfixed = min(
            (i for i, val in enumerate(node.branching_decisions) if val is None),
            default=-1,
        )
        if first_unfixed < 0:
            return ()  # leaf node, nothing to branch
        return node.branching_decisions.split_on(first_unfixed)


class FirstFractionalBranchingStrategy(BranchingStrategy):
    """
    Branch on the first non-integer variable from the relaxed solution.
    If none, fall back to the first unfixed decision variable.
    """

    _FRACTIONAL_TOL = 1e-8

    def make_branching_decisions(self, node: BnBNode) -> tuple[BranchingDecisions, ...]:
        # find first fractional index in relaxed_solution.edge_fractions
        frac_idx = min(
            (
                i
                for i, x in enumerate(node.relaxed_solution.edge_fractions)
                if min(x, 1.0 - x) >= self._FRACTIONAL_TOL
            ),
            default=-1,
        )
        if frac_idx >= 0:
            return tuple(node.branching_decisions.split_on(frac_idx))
        # fallback to first unfixed decision
        first_unfixed = min(
            (i for i, val in enumerate(node.branching_decisions) if val is None),
            default=-1,
        )
        if first_unfixed < 0:
            return ()
        return tuple(node.branching_decisions.split_on(first_unfixed))


class MostFractionalBranchingStrategy(BranchingStrategy):
    """
    Branch on the unfixed edge whose LP value is closest to 0.5.

    Values near 0 or 1 are nearly decided. A value near 0.5 is maximally
    undecided and is therefore a natural branching candidate.

    If multiple edges are equally fractional, choose the edge with the
    greatest travel cost.
    """

    _FRACTIONAL_TOL = 1e-8

    def _sort_key(self, candidate: tuple[int, float, float]):
        return (
            abs(candidate[1] - 0.5),  # closest to 0.5
            -candidate[2],  # greatest weight
            candidate[0],  # lower index
        )

    def make_branching_decisions(self, node: BnBNode) -> tuple[BranchingDecisions, ...]:
        graph = node.relaxed_solution.instance.graph
        edge_weights = tuple(
            float(weight) for _, _, weight in graph.edges.data("weight")
        )

        candidates = [
            (edge_idx, fraction, weight)
            for edge_idx, (fraction, weight, decision) in enumerate(
                zip(
                    node.relaxed_solution.edge_fractions,
                    edge_weights,
                    node.branching_decisions,
                )
            )
            if decision is None
            and self._FRACTIONAL_TOL < fraction < 1.0 - self._FRACTIONAL_TOL
        ]

        if not candidates:
            return ()

        selected_edge_idx = min(candidates, key=self._sort_key)[0]

        return node.branching_decisions.split_on(selected_edge_idx)


# Default branching strategy alias
MyBranchingStrategy = MostFractionalBranchingStrategy  # type: ignore[assignment]
