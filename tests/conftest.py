import networkx as nx
import pytest
from tsp_bnb import BranchingDecisions, CutPool, TSPGraph, TSPInstance


# Arrange
@pytest.fixture
def square_instance() -> TSPInstance:
    """4-city square. Optimal tour = 4.0.

    Edges:
      0-1 (1.0), 1-2 (1.0), 2-3 (1.0), 3-0 (1.0)   # perimeter
      0-2 (1.5), 1-3 (1.5)                          # diagonals
    """
    G: TSPGraph = nx.Graph()
    G.add_weighted_edges_from(
        [
            (0, 1, 1.0),
            (1, 2, 1.0),
            (2, 3, 1.0),
            (3, 0, 1.0),
            (0, 2, 1.5),
            (1, 3, 1.5),
        ]
    )
    return TSPInstance(graph=G, name="square")


@pytest.fixture
def triangle_instance() -> TSPInstance:
    """3-city complete graph. Optimal tour = 3.0. LP is integral (no SECs needed)."""
    G: TSPGraph = nx.complete_graph(3)
    for u, v in G.edges:
        G[u][v]["weight"] = 1.0
    return TSPInstance(graph=G, name="triangle")


@pytest.fixture
def fresh_pool(square_instance: TSPInstance) -> CutPool:
    return CutPool(nodes=square_instance.graph.nodes)


@pytest.fixture
def empty_decisions(square_instance: TSPInstance) -> BranchingDecisions:
    n_edges = square_instance.graph.number_of_edges()
    return BranchingDecisions(n_edges)
