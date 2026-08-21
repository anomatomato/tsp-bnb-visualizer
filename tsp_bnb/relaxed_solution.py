"""
RelaxedSolution Module

This class represents a bounding solution for a TSP branch-and-bound node.
A relaxed solution relaxes integrality constraints to compute a lower bound
on the best feasible tour under given edge fixations.

You should ensure your relaxation solver produces RelaxedSolution objects that:
  1. Keep fixed edge decisions unchanged.
  2. Have `lower_bound` <= the cost of any feasible tour under those decisions.
  3. Pass validation checks in this class.
"""

import math
from collections.abc import Sequence
from enum import StrEnum, auto
from typing import Self

import highspy
import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .data_schema import TSPInstance

INFEASIBLE_LOWER_BOUND = math.inf
TOL = 1e-8


class SolveStatus(StrEnum):
    OPTIMAL = auto()
    TIME_LIMIT = auto()
    INFEASIBLE = auto()


class RelaxedSolution(BaseModel):
    """
    A relaxation of the TSP under some fixations.

    For LP relaxation: edge_fractions are the LP variables, objective_value
    is the LP objective, and lower_bound == objective_value.

    For other relaxations (Lagrangian, 1-tree): edge_fractions may be a
    reference feasible x for the LP part, and lower_bound may come from a
    different subproblem — so lower_bound < objective_value is allowed.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    instance: TSPInstance
    edge_fractions: Sequence[float] = Field(
        ..., description="One fractional value per edge in instance.graph, in [0,1]"
    )
    lower_bound: float = Field(
        ..., description="Lower bound on optimal tour cost under the edge fixations"
    )
    status: SolveStatus = Field(..., description="Status of the relaxation solver")
    basis: highspy.HighsBasis | None = Field(
        default=None, description="Solver basis to propagate to children nodes"
    )

    # --- Validators ---

    @field_validator("edge_fractions")
    @classmethod
    def _validate_edge_fractions(cls, edge_fractions: Sequence[float]):
        if not all(0 <= edge <= 1 for edge in edge_fractions):
            raise ValueError("edge_fractions have to be in [0,1]")
        return edge_fractions

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
            status=SolveStatus.INFEASIBLE,
        )

    # --- Queries ---

    def is_infeasible(self) -> bool:
        """
        Return True if this solution represents an infeasible branch.
        """
        return self.status == SolveStatus.INFEASIBLE

    def is_integral(self, atol: float = TOL) -> bool:
        """
        Return True if all fractions are integers (0 or 1).
        """
        if self.is_infeasible():
            return False
        return all(min(frac, 1 - frac) < atol for frac in self.edge_fractions)

    def is_feasible_tour(self, atol: float = TOL) -> bool:
        """True if integral AND forms a single Hamiltonian cycle.

        The LP enforces degree==2 for every node, so an integral solution is a
        collection of node-disjoint cycles. It's a valid tour iff it's connected
        (one cycle covering all nodes). Disjoint subtours are integral but not
        a valid tour — the cut loop failed to eliminate them.
        """
        if not self.is_integral(atol):
            return False
        graph = self.as_graph(threshold=0.5)
        n_nodes = self.instance.graph.number_of_nodes()
        return nx.is_connected(graph) and graph.number_of_edges() == n_nodes

    def as_graph(self, threshold: float = 0.1) -> nx.Graph[int]:
        """Return the current LP solution as a graph (edges with x > threshold)."""
        graph = nx.Graph()
        graph.add_nodes_from(self.instance.graph.nodes)
        for (u, v), frac in zip(self.instance.graph.edges, self.edge_fractions):
            if frac > threshold:
                graph.add_edge(u, v, x=frac)
        return graph

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
