"""SVG rendering functions for BnB state. Stateless, NetworkX + matplotlib."""

from pathlib import Path
from typing import cast

import matplotlib.pyplot as plt
import networkx as nx

from ..data_schema import TSPInstance


def compute_circular_positions(instance: TSPInstance) -> dict[int, tuple[float, float]]:
    """Compute fixed circular layout via ``nx.circular_layout``. Reuse for all renders.

    Not weight-aware — places nodes evenly on a circle. Use
    :func:`compute_kamada_kawai_positions` when edge weights should influence
    placement (standard for TSP).

    Returns ``dict[node_id -> (x, y)]`` with plain Python floats.
    """
    G = cast(nx.Graph, instance.graph)
    # store_pos_as="pos" persists layout on graph, but we return the dict
    # and pass it explicitly to every render — guarantees identical positions.
    raw = nx.circular_layout(G)
    pos = {i: (float(p[0]), float(p[1])) for i, p in raw.items()}
    return pos


def compute_kamada_kawai_positions(
    instance: TSPInstance,
) -> dict[int, tuple[float, float]]:
    """Compute fixed weight-aware layout via ``nx.kamada_kawai_layout``.

    Kamada-Kawai treats the ``weight`` edge attribute as graph distance —
    correct TSP semantics (heavier edges = farther apart). Deterministic:
    same input always produces the same output. Compute once and pass the
    result to every render so iterations stay visually comparable.

    Returns ``dict[node_id -> (x, y)]`` with plain Python floats.
    """
    G = cast(nx.Graph, instance.graph)
    # store_pos_as="pos" persists layout on graph, but we return the dict
    # and pass it explicitly to every render — guarantees identical positions.
    raw = nx.kamada_kawai_layout(G)
    pos = {i: (float(p[0]), float(p[1])) for i, p in raw.items()}
    return pos


def render_lp_solution(
    instance: TSPInstance,
    positions: dict[int, tuple[float, float]],
    edge_fractions: list[float],
    path: Path,
    *,
    threshold: float = 0.01,
    show_edge_labels: bool = False,
    show_node_labels: bool = True,
) -> None:
    """Render fractional LP solution as SVG via ``nx.draw_networkx_edges``.

    Binary color scheme (no colormap):
      - ``x_ij = 1.0`` (integral IN)  → thick blue (width 5)
      - ``0 < x_ij < 1`` (fractional) → red, width ∝ ``x_ij``
      - ``x_ij = 0``                  → not drawn

    Edges with fraction ≤ ``threshold`` are skipped (zero edges not drawn).
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    G = cast(nx.Graph, instance.graph)

    integral_in = [
        (e, x)
        for e, x in zip(G.edges(), edge_fractions, strict=True)
        if x > 1.0 - threshold
    ]
    fractional = [
        (e, x)
        for e, x in zip(G.edges(), edge_fractions, strict=True)
        if threshold < x <= 1.0 - threshold
    ]

    if integral_in:
        edge_list, _ = zip(*integral_in, strict=True)
        nx.draw_networkx_edges(
            G,
            positions,
            ax=ax,
            edgelist=list(edge_list),
            width=5,
            edge_color="tab:blue",
        )

    if fractional:
        edge_list, x_list = zip(*fractional, strict=True)
        nx.draw_networkx_edges(
            G,
            positions,
            ax=ax,
            edgelist=list(edge_list),
            width=[x * 5 for x in x_list],  # per-edge width, scaled by fraction
            edge_color="tab:red",
            alpha=0.8,  # transparency
        )

    nx.draw_networkx_nodes(G, positions, ax=ax, node_size=200, node_color="black")
    if show_node_labels:
        nx.draw_networkx_labels(G, positions, ax=ax, font_size=9, font_color="white")
    if show_edge_labels:
        nx.draw_networkx_edge_labels(
            G,
            positions,
            ax=ax,
            font_size=7,
            edge_labels={e: f"{x:.2f}" for e, x in integral_in + fractional},
            label_pos=0.5,
        )

    ax.set_aspect("equal")
    ax.axis(False)
    _save_svg(fig, path)


def render_tour(
    instance: TSPInstance,
    positions: dict[int, tuple[float, float]],
    edge_selection: list[int],
    path: Path,
    *,
    show_edge_labels: bool = False,
    show_node_labels: bool = True,
) -> None:
    """Render tour as SVG: thick blue edges for selected, thin gray for rest.

    Edge labels (weights) shown only on selected edges (N labels, no clutter
    even for large N). Weights are formatted ``:.1f`` and default to 1.0
    when the ``weight`` attribute is missing.
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    G = cast(nx.Graph, instance.graph)
    included_edges = [
        e for e, x in zip(G.edges(), edge_selection, strict=True) if x == 1
    ]

    if included_edges:
        nx.draw_networkx_edges(
            G,
            positions,
            ax=ax,
            edgelist=included_edges,
            width=5,  # per-edge width, scaled by fraction
            edge_color="tab:blue",
        )

    nx.draw_networkx_nodes(G, positions, ax=ax, node_size=200, node_color="black")
    if show_node_labels:
        nx.draw_networkx_labels(G, positions, ax=ax, font_size=9, font_color="white")
    if show_edge_labels:
        tour_labels = {e: f"{G.edges[e].get('weight'):.1f}" for e in included_edges}
        nx.draw_networkx_edge_labels(
            G,
            positions,
            ax=ax,
            font_size=7,
            edge_labels=tour_labels,
            label_pos=0.5,
        )

    ax.set_aspect("equal")
    ax.axis(False)
    _save_svg(fig, path)


def _save_svg(fig: plt.Figure, path: Path) -> None:
    """Save matplotlib figure as SVG, ensure parent dir exists, close figure.

    ``bbox_inches="tight"`` crops the SVG to actual content so dimensions
    match the graph rather than ``figsize`` — consistent across renders.
    ``plt.close(fig)`` frees figure memory; essential because render
    functions are called once per BnB node (hundreds/thousands of times).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path, format="svg", bbox_inches="tight"
    )  # bbox_inches=tight crops to content
    plt.close(fig)
