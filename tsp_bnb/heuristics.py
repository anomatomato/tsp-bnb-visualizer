"""
Heuristics for the TSP Branch-and-Bound solver.

Heuristics produce feasible tours (upper bounds on the optimal tour cost) to
tighten pruning in the BnB search. Construction heuristics (NN, Christofides)
build a tour from the instance; improvement heuristics (2-opt) refine an
existing tour. LP-guided heuristics use the fractional LP solution to guide
tour construction.

Subclass `Heuristics` and override `search(instance, relaxed)` to return a
feasible `TSPSolution` (or None if no tour could be constructed).
"""

from abc import ABC, abstractmethod
from typing import cast

import networkx as nx
from networkx.algorithms import approximation as approx

from ._utils import edge_selection_to_cycle
from .data_schema import TSPGraph, TSPInstance, TSPSolution
from .relaxed_solution import RelaxedSolution


class Heuristics(ABC):
    """Abstract base for TSP heuristics.

    A heuristic produces a feasible tour (a `TSPSolution`) that serves as an
    upper bound on the optimal tour cost, enabling the BnB to prune nodes
    whose LP lower bound is no better.

    Construction heuristics (e.g. `NearestNeighborHeuristic`) ignore the
    `relaxed` argument and build a tour directly from the instance.
    LP-guided heuristics (e.g. LP-rounding) use `relaxed` to construct a tour
    from the fractional LP solution. `TwoOptImproved` wraps any heuristic
    with a 2-opt local-search improvement pass.
    """

    @abstractmethod
    def search(
        self, instance: TSPInstance, relaxed: RelaxedSolution | None = None
    ) -> TSPSolution | None:
        """Return a feasible `TSPSolution`, or None if no tour was found.

        Args:
            instance: The TSP instance to solve.
            relaxed: The node's LP relaxation solution, if available.
                Construction heuristics may ignore this; LP-guided heuristics
                require it. None at the root before any LP solve.
        """
        ...


class NearestNeighborHeuristic(Heuristics):
    """Nearest Neighbor construction heuristic.

    Starting from an arbitrary city, repeatedly extend the tour by the
    nearest unvisited city until all cities are visited, then close the
    cycle. O(n^2). Typically ~25% above optimal; pair with `TwoOptImproved`
    to reach ~5% above optimal.

    Uses `networkx.algorithms.approximation.greedy_tsp`, which is the
    textbook NN (despite the name). The `relaxed` argument is ignored —
    NN builds from the instance alone.
    """

    def search(
        self, instance: TSPInstance, relaxed: RelaxedSolution | None = None
    ) -> TSPSolution | None:
        G: nx.Graph = cast(nx.Graph, instance.graph)
        nn_cycle: list[int] = approx.greedy_tsp(G, weight="weight")

        solution = TSPSolution.from_cycle(G, nn_cycle)

        return solution


class TwoOptImproved(Heuristics):
    """Wrap any heuristic with a 2-opt local-search improvement pass.

    Runs the inner heuristic to get an initial tour, then applies `two_opt`
    to refine it. This lets the BnB compose "any construction + 2-opt"
    without each construction heuristic knowing about 2-opt:

        heuristic = TwoOptImproved(NearestNeighborHeuristic())
        heuristic = TwoOptImproved(ChristofidesHeuristic())
    """

    def __init__(self, inner: Heuristics):
        self.inner = inner

    def search(
        self, instance: TSPInstance, relaxed: RelaxedSolution | None = None
    ) -> TSPSolution | None:
        init_sol = self.inner.search(instance, relaxed)
        if init_sol is None:
            return None

        G = cast(nx.Graph, instance.graph)
        cycle = edge_selection_to_cycle(G, init_sol.edge_selection)
        improved_cycle = two_opt(instance.graph, cycle)

        solution = TSPSolution.from_cycle(G, improved_cycle)
        return solution


def two_opt(G: TSPGraph, cycle: list[int]) -> list[int]:
    """Improve a tour with 2-opt local search.

    Repeatedly removes two non-adjacent edges (A,B) and (C,D) from the tour
    and reconnects as (A,C) and (B,D), reversing the segment B..C, whenever
    this reduces the tour cost. Stops at a local optimum (no improving move).

    O(n^2) per pass; typically a few passes to converge. Reaches ~5% above
    optimal when started from an NN tour.

    Args:
        G: The complete weighted TSP graph.
        cycle: A closed node cycle (last node == first node).

    Returns:
        The improved closed node cycle (mutated in place).
    """
    n = len(cycle) - 1  # cycle is closed: last == first
    improved = True
    while improved:
        improved = False
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
                if delta < -1e-9:  # improvement
                    cycle[i + 1 : j + 1] = reversed(cycle[i + 1 : j + 1])
                    improved = True
    return cycle
