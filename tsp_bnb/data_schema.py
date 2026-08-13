from collections.abc import Sequence
from typing import TYPE_CHECKING, TypedDict

import networkx as nx
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    field_validator,
)

from ._utils import cycle_to_edge_selection


class NodeData(TypedDict):
    pass


class EdgeData(TypedDict):
    """Every edge in a TSP graph carries a positive weight."""

    weight: float


# typeshed PR python/typeshed#15660 (merged 2026-05-11) added generic
# `nx.Graph[Node, NodeData, EdgeData]` to the networkx stubs. Type checkers
# (mypy / pyrefly / pyright) see the full generic. At runtime, `nx.Graph`
# has no `__class_getitem__`, so we must guard the subscripted alias with
# `TYPE_CHECKING` and fall back to the bare class. The class annotation
# `graph: TSPGraph` then resolves to `nx.Graph` at class def time, which
# Pydantic accepts via `arbitrary_types_allowed=True`.
if TYPE_CHECKING:
    type TSPGraph = nx.Graph[int, NodeData, EdgeData]
else:
    type TSPGraph = nx.Graph


class TSPInstance(BaseModel):
    """Traveling Salesman Problem instance."""

    graph: TSPGraph = Field(..., description="NetworkX graph with edge weights")
    name: str = Field(default="tsp_instance", description="Instance name")

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    @field_validator("graph", mode="before")
    @classmethod
    def is_valid_graph(cls, g: TSPGraph):
        n = g.number_of_nodes()
        if n < 3:
            raise ValueError("Graph needs at least 3 nodes")
        if g.number_of_edges() != n * (n - 1) // 2:
            raise ValueError("Invalid graph: not complete")
        if not all(weight > 0 for _, _, weight in g.edges.data("weight")):
            raise ValueError(
                "Invalid graph: every edge requires a positive 'weight' attribute"
            )
        return g


class TSPSolution(BaseModel):
    """Traveling Salesman Problem Solution."""

    edge_selection: Sequence[int] = Field(
        ..., description="One integral value per edge in instance.graph, in [0,1]"
    )
    cost: NonNegativeFloat = Field(..., description="The overall cost of the tour.")

    model_config = ConfigDict(frozen=True)

    @field_validator("edge_selection", mode="before")
    @classmethod
    def are_valid_edge_values(cls, edge_selection: Sequence[int]):
        if not all(val in {0, 1} for val in edge_selection):
            raise ValueError("All edge_values need to be either 0 or 1")
        return edge_selection

    @classmethod
    def from_cycle(cls, G: nx.Graph, cycle: list[int]) -> "TSPSolution":
        """Construct from a node cycle. Computes edge_selection and cost."""
        selection = cycle_to_edge_selection(G, cycle)
        cost = sum(G[n][nbr]["weight"] for n, nbr in nx.utils.pairwise(cycle))

        return cls(edge_selection=selection, cost=cost)
