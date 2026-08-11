"""
Heuristics Module

In branch-and-bound, a relaxation gives an upper bound on the best objective in a branch.
To tighten pruning, you need feasible (integral) solutions to serve as lower bounds.
Instead of waiting for an integral node, you can derive feasible solutions from the relaxation
(e.g., rounding, greedy inclusion) to improve search efficiency.

You can implement heuristics by subclassing `Heuristics` and overriding `search(instance, node)`.
`search` should yield zero or more feasible `RelaxedSolution` objects.
"""

from abc import ABC, abstractmethod
from typing import cast

import networkx as nx
from networkx.algorithms import approximation as approx

from .data_schema import TSPGraph, TSPInstance, TSPSolution
from .relaxed_solution import RelaxedSolution


class Heuristics(ABC):
    """
    Abstract base for heuristic generators.

    Implement `search` to produce feasible solutions from a node's relaxed solution.
    """

    @abstractmethod
    def search(self, instance: TSPInstance, relaxed: RelaxedSolution) -> TSPSolution:
        """
        Return a tuple of feasible `HeuristicSolution` objects for pruning.
        """
        ...


class NearestNeighborHeuristic(Heuristics):
    """
    Nearest Neighbor heuristic.

    - The algorithm adds a node to the solution at every iteration.
    - The algorithm selects a node not already in the cycle whose connection to the previous node adds the least cost to the cycle.
    """

    def search(self, instance: TSPInstance, relaxed: RelaxedSolution) -> TSPSolution:
        G: nx.Graph = cast(nx.Graph, instance.graph)
        nn_cycle: list[int] = approx.greedy_tsp(G, weight="weight")

        solution = TSPSolution.from_cycle(G, nn_cycle)

        return solution


def two_opt(G: TSPGraph, cycle: list[int]) -> list[int]:
    """Improve a tour with 2-opt local search. Returns improved cycle."""
    n = len(cycle) - 1  # cycle is closed: last == first
    improved = True
    while improved:
        for i in range(n - 1):
            for j in range(i + 2, n):
                # Edges (cycle[i], cycle[i+1]) and (cycle[j], cycle[j+1])
                # Reconnect as (cycle[i], cycle[j]) and (cycle[i+1], cycle[j+1])
                a, b, c, d = cycle[i], cycle[i + 1], cycle[j], cycle[j + 1]
                delta = (
                    G[a][c]["weight"]
                    + G[b][d]["weight"]
                    - G[a][b]["weight"]
                    - G[c][d]["weight"]
                )
                if delta < 0:  # improvement
                    cycle[i + 1 : j + 1] = reversed(cycle[i + 1 : j + 1])
                    improved = True
    return cycle


# <Solution>


# MyHeuristic = NearestNeighborHeuristic  # type: ignore[assignment]
# </Solution>
