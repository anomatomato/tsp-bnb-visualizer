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
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .data_schema import TSPInstance

INFEASIBLE_LOWER_BOUND = math.inf
TOL = 1e-8


class RelaxedSolution(BaseModel):
    """
    A relaxation of the TSP under some fixations.

    For LP relaxation: edge_fractions are the LP variables, objective_value
    is the LP objective, and lower_bound == objective_value.

    For other relaxations (Lagrangian, 1-tree): edge_fractions may be a
    reference feasible x for the LP part, and lower_bound may come from a
    different subproblem — so lower_bound < objective_value is allowed.
    """

    model_config = ConfigDict(frozen=True)

    instance: TSPInstance
    edge_fractions: Sequence[float] = Field(
        ..., description="One fractional value per edge in instance.graph, in [0,1]"
    )
    lower_bound: float = Field(
        ..., description="Lower bound on optimal tour cost under the edge fixations"
    )

    # --- Validators ---

    @model_validator(mode="after")
    def _validate_consistency(self) -> Self:
        n_edges = self.instance.graph.number_of_edges()
        if len(self.edge_fractions) != n_edges:
            raise ValueError(
                f"`edge_fractions` length ({len(self.edge_fractions)}) "
                f"must match number of edges ({n_edges})."
            )

        if math.isfinite(self.lower_bound):
            actual = self.objective_value
            if self.lower_bound > actual + TOL:
                raise ValueError(
                    f"lower_bound ({self.lower_bound}) cannot exceed "
                    f"objective_value ({actual})."
                )

        return self

    # --- Properties ---

    @property
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

    # --- Factories ---

    @staticmethod
    def create_infeasible(instance: TSPInstance) -> "RelaxedSolution":
        """
        Return a RelaxedSolution marking an infeasible branch.
        Its `lower_bound` is infinity and `edge_fractions` is all zeros.
        """
        return RelaxedSolution(
            instance=instance,
            edge_fractions=[0.0] * instance.graph.number_of_edges(),
            lower_bound=INFEASIBLE_LOWER_BOUND,
        )

    # --- Queries ---

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

    def is_integral(self, atol: float = TOL) -> bool:
        """
        Return True if all fractions are integers (0 or 1).
        """
        if self.is_infeasible():
            return False
        return all(min(frac, 1 - frac) < atol for frac in self.edge_fractions)

    # --- Display ---

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
