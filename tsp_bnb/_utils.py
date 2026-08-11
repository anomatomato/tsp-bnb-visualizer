from collections.abc import Sequence

import networkx as nx


def cycle_to_edge_selection(G: nx.Graph, cycle: list[int]) -> list[int]:
    """Convert a node cycle into a 0/1 vector aligned with `G.edges()`."""
    selection = [0] * G.number_of_edges()
    edge_idx = {frozenset((u, v)): i for i, (u, v) in enumerate(G.edges())}
    for n, nbr in nx.utils.pairwise(cycle):
        selection[edge_idx[frozenset((n, nbr))]] = 1

    return selection


def edge_selection_to_cycle(G: nx.Graph, selection: Sequence[int]) -> list[int]:
    """Convert a 0/1 vector aligned with `G.edges()` to a node cycle."""
    # Build adjacency from selected edges (each node has degree 2 in a valid tour)
    adj: dict[int, list[int]] = {n: [] for n in G.nodes()}
    for (u, v), sel in zip(G.edges(), selection, strict=True):
        if sel == 1:
            adj[u].append(v)
            adj[v].append(u)

    # Walk the cycle from an arbitrary start
    start = next(iter(G.nodes()))
    cycle = [start]
    prev: int | None = None
    current = start
    while True:
        neighbors = adj[current]
        nxt = neighbors[0] if neighbors[0] != prev else neighbors[1]
        if nxt == start:
            cycle.append(start)  # close the cycle
            break
        cycle.append(nxt)
        prev = current
        current = nxt
    return cycle
