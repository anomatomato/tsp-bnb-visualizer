from typing import TYPE_CHECKING, TypeAlias, TypedDict

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    TSPGraph: TypeAlias = nx.Graph[int, NodeData, EdgeData]
else:
    TSPGraph = nx.Graph


class TSPInstance(BaseModel):
    """Traveling Salesman Problem instance."""

    graph: TSPGraph = Field(..., description="NetworkX graph with edge weights")
    name: str = Field(default="tsp_instance", description="Instance name")

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    @field_validator("graph", mode="before")
    @classmethod
    def is_valid_graph(cls, g: TSPGraph):
        n = g.number_of_nodes()
        if n < 2:
            raise ValueError("Graph needs at least 2 nodes")
        if g.number_of_edges() != n * (n - 1) // 2:
            raise ValueError("Invalid graph: not complete")
        if not all(weight > 0 for _, _, weight in g.edges.data("weight")):
            raise ValueError(
                "Invalid graph: every edge requires a positive 'weight' attribute"
            )
        return g


# class City(BaseModel):
#     x: float
#     y: float
#     name: str = Field(default="City")

# class TSPInstance(BaseModel):
#     """Traveling Salesman Problem instance."""
#     cities: list[City] = Field(..., description="List of cities")
#     distance_matrix: list[list[float]] = Field(..., description="Precomputed distance matrix")
#     optimal_known: float | None = Field(None, description="Known optimal solution value")

# class TSPSolution(BaseModel):
#     """Traveling Salesman Problem Solution."""
#     path: Sequence[City]
#     cost: float
