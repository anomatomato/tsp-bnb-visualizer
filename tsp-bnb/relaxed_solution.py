"""
RelaxedSolution Module

This class represents a bounding solution for a knapsack branch.
A relaxed solution may relax capacity or integrality constraints to
compute an upper bound on the best feasible 0/1 solution under given fixations.

You should ensure your relaxation solver produces RelaxedSolution objects that:
  1. Keep fixed decisions unchanged.
  2. Have `lower_bound` <= the value of any feasible 0/1 solution under those decisions.
  3. Pass validation checks in this class.
"""

import math
from collections.abc import Sequence
from functools import cached_property

from pydantic import BaseModel

from .data_schema import ConfigDict, TSPInstance

INFEASIBLE_LOWER_BOUND = float("inf")


class RelaxedSolution(BaseModel):
    """
    Encapsulates a possibly-relaxed assignment (`selection`) and its bound.

    Args:
        instance: the TSPInstance
        selection: a sequence of floats in [0,1], one per item;
                   fixed items must match your fixation (0 or 1).
        lower_bound: a lower bound on the value of any 0/1 solution
                     consistent with `selection` fixations.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        instance: TSPInstance,
        edge_fractions: Sequence[float],
        lower_bound: float,
    ):
        if len(edge_fractions) != instance.graph.number_of_edges():
            raise ValueError("`selection` length must match number of edges.")
        self.instance = instance
        self.edge_fractions = list(edge_fractions)
        self.lower_bound = lower_bound

        # Validate consistency: actual value must exceed or equal lower bound.
        actual = self.objective_value
        if math.isfinite(self.lower_bound) and self.lower_bound > actual + 1e-8:
            raise ValueError(
                f"Actual value {actual} is less than lower_bound {self.lower_bound}."
            )

    @cached_property
    def objective_value(self) -> float:
        """
        Compute total cost = sum(edge.weight * fraction).
        """
        return sum(
            weight * frac
            for (_, _, weight), frac in zip(
                self.instance.graph.edges.data("weight"), self.edge_fractions
            )
        )

    @staticmethod
    def create_infeasible(instance: TSPInstance) -> "RelaxedSolution":
        """
        Return a RelaxedSolution marking an infeasible branch.
        Its `lower_bound` is infinity and `selection` is all zeros.
        """
        return RelaxedSolution(
            instance,
            [0.0] * instance.graph.number_of_edges(),
            lower_bound=INFEASIBLE_LOWER_BOUND,
        )

    def is_infeasible(self) -> bool:
        """
        Return True if this solution represents an infeasible branch.
        """
        return self.lower_bound == INFEASIBLE_LOWER_BOUND

    def has_valid_fractions(self) -> bool:
        """
        Return True if selections
        are in [0,1]. Returns False for infeasible marker.
        """
        if self.is_infeasible():
            return False
        return all(0.0 <= frac <= 1.0 for frac in self.edge_fractions)

    def is_integral(self, atol: float = 1e-10) -> bool:
        """
        Return True if all fractions are integers (0 or 1).
        """
        if self.is_infeasible():
            return False
        return all(min(frac, 1 - frac) < atol for frac in self.edge_fractions)

    def __repr__(self) -> str:
        return f"RelaxedSolution(lb={self.lower_bound:.4f}, {self})"

    def __str__(self) -> str:
        """
        String representation like "[1|0.5|0|...]".
        Fractions are shown with one decimal if non-integer.
        """
        parts = []
        for frac in self.edge_fractions:
            if frac == int(frac):
                parts.append(str(int(frac)))
            else:
                parts.append(f"{frac:.1f}")
        return "[" + "|".join(parts) + "]"

    # def copy(self) -> "RelaxedSolution":
    #     """
    #     Return a deep copy of this RelaxedSolution.
    #     """
    #     return RelaxedSolution(self.instance, self.selection.copy(), self.lower_bound)
