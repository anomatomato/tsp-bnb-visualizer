from typing import TypedDict

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NodeData(TypedDict): ...


class EdgeData(TypedDict):
    """Every edge in a TSP graph carries a positive weight."""

    weight: float


# from typing import Sequence


class TSPInstance(BaseModel):
    """Traveling Salesman Problem instance."""

    graph: nx.Graph[float, NodeData, EdgeData] = Field(
        ..., description="NetworkX graph with edge weights"
    )
    name: str = Field(default="tsp_instance", description="Instance name")

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    @field_validator("graph", mode="before")
    @classmethod
    def is_valid_graph(cls, g: nx.Graph[float, NodeData, EdgeData]):
        n = g.number_of_nodes()
        if n < 2:
            raise ValueError("Graph needs at least 2 nodes")
        if g.number_of_edges() != n * (n - 1) / 2:
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
