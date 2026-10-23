"""Node outcome export: prune/infeasible reasons, prune metadata, branch edges.

Callback-level tests drive ``BnBSerializer`` events directly with hand-built
``RelaxedSolution`` objects (no HiGHS, no search). Integration tests run full
searches and validate the written ``bnb_state.json`` (HiGHS, ``@pytest.mark.slow``).
"""

from pathlib import Path

import pytest
from tsp_bnb.bnb import TSPBnb
from tsp_bnb.bnb_nodes import BnBNode, InfeasibleReason, NodeStatus, PruneReason
from tsp_bnb.branching_decisions import BranchingDecisions, branched_edge_index
from tsp_bnb.branching_strategy import MostFractionalBranchingStrategy
from tsp_bnb.data_schema import TSPInstance
from tsp_bnb.export import BnBSerializer
from tsp_bnb.export.models import BnBRunData
from tsp_bnb.heuristics import NearestNeighborHeuristic, TwoOptImproved
from tsp_bnb.open_nodes import OpenNodeQueue, best_bound_order, depth_first_order
from tsp_bnb.relaxation import LPRelaxation
from tsp_bnb.relaxed_solution import RelaxedSolution, SolveStatus

# --- Fixtures and helpers ------------------------------------------------------


@pytest.fixture
def square4_instance() -> TSPInstance:
    """4-city complete graph whose root LP ties the warm-start incumbent.

    Edges: (0,1)=2, (0,2)=3, (0,3)=2, (1,2)=2, (1,3)=3, (2,3)=2.
    Optimal tour 0-1-2-3-0 = 8; the NN + 2-opt warm start also finds 8, and
    the root LP (after the SEC cut loop) reaches the integral perimeter 8, so
    the root is an immediate node-bound prune. K4 has no feasible fractional
    vertex (each node has only 3 edges), so this instance never branches.
    """
    import networkx as nx
    from tsp_bnb.data_schema import TSPGraph

    g: TSPGraph = nx.Graph()
    g.add_weighted_edges_from(
        [
            (0, 1, 2.0),
            (0, 2, 3.0),
            (0, 3, 2.0),
            (1, 2, 2.0),
            (1, 3, 3.0),
            (2, 3, 2.0),
        ]
    )
    return TSPInstance(graph=g, name="square4")


def _objective(instance: TSPInstance, fractions: list[float]) -> float:
    return sum(
        weight * frac
        for (_, _, weight), frac in zip(instance.graph.edges.data("weight"), fractions)
    )


def _feasible_relaxation(
    instance: TSPInstance, fractions: list[float]
) -> RelaxedSolution:
    return RelaxedSolution(
        instance=instance,
        edge_fractions=fractions,
        lower_bound=_objective(instance, fractions),
        status=SolveStatus.OPTIMAL,
    )


def _make_node(
    instance: TSPInstance,
    fractions: list[float],
    *,
    status: NodeStatus | None = None,
    node_id: int = 1,
    parent_id: int | None = None,
) -> BnBNode:
    node = BnBNode(
        relaxed_solution=_feasible_relaxation(instance, fractions),
        branching_decisions=BranchingDecisions(instance.graph.number_of_edges()),
        depth=1 if parent_id is not None else 0,
        node_id=node_id,
        parent_id=parent_id,
    )
    node.status = status
    return node


def _flatten(root) -> list:
    """Depth-first flatten of the recursive NodeVisData tree."""
    out = []
    stack = [root]
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(node.children)
    return out


def _make_bnb(
    instance: TSPInstance,
    serializer: BnBSerializer | None,
    *,
    priority=best_bound_order,
) -> TSPBnb:
    return TSPBnb(
        instance=instance,
        relaxation_cls=LPRelaxation,
        node_queue=OpenNodeQueue(priority=priority),
        branching_strategy=MostFractionalBranchingStrategy(),
        root_heuristics=TwoOptImproved(NearestNeighborHeuristic()),
        serializer=serializer,
    )


# --- branched_edge_index helper ------------------------------------------------


def test_branched_edge_index_finds_split_edge() -> None:
    decisions = BranchingDecisions(6)
    left, right = decisions.split_on(4)
    assert branched_edge_index((left, right)) == 4, "the pair differs exactly on edge 4"
    assert branched_edge_index(()) is None, "no branches means no branched edge"


# --- Callback-level tests ------------------------------------------------------


def test_processed_branched_node_exports_branched_edge(
    tmp_path: Path, square_instance: TSPInstance
) -> None:
    serializer = BnBSerializer(square_instance, output_root=tmp_path)
    fractions = [1.0, 0.0, 1.0, 0.5, 0.5, 0.0]
    node = _make_node(square_instance, fractions, status=NodeStatus.BRANCHED)
    node.branched_edge = 4

    serializer.on_new_node_in_tree(node, iteration=1)
    serializer.on_node_processed(node, lb=3.2, ub=4.0, iteration=2)

    data = serializer._node_data[node.node_id]
    assert data.branched_edge == 4, "branched node must record its branch edge"
    assert data.prune_reason is None, "branched node has no prune reason"
    assert data.infeasible_reason is None, "branched node has no infeasibility reason"
    assert data.pruned_at is None, "branched node is never pruned"


def test_processed_pruned_node_exports_node_bound_reason(
    tmp_path: Path, square_instance: TSPInstance
) -> None:
    serializer = BnBSerializer(square_instance, output_root=tmp_path)
    fractions = [1.0, 0.0, 1.0, 0.5, 0.5, 0.0]
    node = _make_node(square_instance, fractions, status=NodeStatus.PRUNED)

    serializer.on_new_node_in_tree(node, iteration=1)
    serializer.on_node_processed(node, lb=4.3, ub=4.0, iteration=17)

    data = serializer._node_data[node.node_id]
    assert data.prune_reason is PruneReason.NODE_BOUND, (
        "processed prune is a per-node bound prune"
    )
    assert data.pruned_at == 17, (
        "node-bound prune is pruned at its processing iteration"
    )
    assert data.processed_at == 17, "node-bound prune was processed"
    assert data.ub == 4.0, "ub is the incumbent that killed the node"
    assert data.branched_edge is None, "pruned node records no branch edge"


def test_processed_infeasible_lp_exports_lp_reason(
    tmp_path: Path, square_instance: TSPInstance
) -> None:
    serializer = BnBSerializer(square_instance, output_root=tmp_path)
    relaxed = RelaxedSolution.create_infeasible(square_instance)
    node = BnBNode(
        relaxed_solution=relaxed,
        branching_decisions=BranchingDecisions(square_instance.graph.number_of_edges()),
        depth=0,
        node_id=2,
        parent_id=None,
    )
    node.status = NodeStatus.INFEASIBLE

    serializer.on_new_node_in_tree(node, iteration=1)
    serializer.on_node_processed(node, lb=float("inf"), ub=4.0, iteration=5)

    data = serializer._node_data[node.node_id]
    assert data.infeasible_reason is InfeasibleReason.LP_INFEASIBLE, (
        "unsolvable LP must record lp_infeasible"
    )
    assert data.relaxed_solution is None, "an infeasible LP has no fractions to show"
    assert data.prune_reason is None, "infeasible is not a prune"


def test_processed_infeasible_subtours_exports_subtours_reason(
    tmp_path: Path, two_triangles_instance: TSPInstance
) -> None:
    serializer = BnBSerializer(two_triangles_instance, output_root=tmp_path)
    # 1.0 on the six intra-triangle edges, 0.0 on the nine cross edges:
    # integral but two disconnected subtours. Graph edge order is adjacency
    # order, so fractions must be derived from actual edge membership.
    triangle_edges = {
        frozenset(e) for e in [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]
    }
    fractions = [
        1.0 if frozenset((u, v)) in triangle_edges else 0.0
        for u, v in two_triangles_instance.graph.edges
    ]
    node = _make_node(two_triangles_instance, fractions, status=NodeStatus.INFEASIBLE)

    serializer.on_new_node_in_tree(node, iteration=1)
    serializer.on_node_processed(node, lb=6.0, ub=24.0, iteration=3)

    data = serializer._node_data[node.node_id]
    assert data.infeasible_reason is InfeasibleReason.SUBTOURS, (
        "integral-but-disconnected solution must record subtours"
    )
    assert data.relaxed_solution is not None, "a solved LP keeps its snapshot"
    assert data.relaxed_solution.is_integral_tour is False, (
        "two disjoint triangles are not one tour"
    )


def test_global_pruned_leftover_exports_incumbent_and_iteration(
    tmp_path: Path, square_instance: TSPInstance
) -> None:
    serializer = BnBSerializer(square_instance, output_root=tmp_path)
    fractions = [1.0, 0.0, 1.0, 0.5, 0.5, 0.0]
    node = _make_node(square_instance, fractions, status=NodeStatus.PRUNED)

    # A leftover shares the last processed iteration's entry, so the search
    # loop always processes at least one node before a global prune.
    processed = _make_node(
        square_instance, fractions, status=NodeStatus.BRANCHED, node_id=7
    )
    serializer.on_new_node_in_tree(processed, iteration=1)
    serializer.on_node_processed(processed, lb=4.0, ub=426.0, iteration=38)

    serializer.on_new_node_in_tree(node, iteration=1)
    serializer.on_node_global_pruned(node, iteration=39, incumbent=426.0, lb=428.0)

    assert serializer._iteration_entries[-1].global_pruned_node_ids == [node.node_id], (
        "the leftover is appended to the shared final iteration entry"
    )

    data = serializer._node_data[node.node_id]
    assert data.status is NodeStatus.PRUNED, "leftover is marked pruned"
    assert data.prune_reason is PruneReason.GLOBAL_BOUND, (
        "queue leftovers are pruned by the global bound"
    )
    assert data.pruned_at == 39, "leftover records the global-prune iteration"
    assert data.ub == 426.0, "leftover ub is the incumbent that closed the queue"
    assert data.lb == 428.0, "leftover lb is the queue-wide bound that closed the queue"
    assert data.processed_at is None, "leftovers are never processed"
    assert node.node_id not in serializer._processing_order, (
        "leftovers never enter the processing order"
    )
    assert data.fixed_edges == [None] * 6, "leftover fixations are exported"
    assert data.relaxed_solution is not None, "creation-time LP is real data"


def test_global_pruned_leftover_without_incumbent_keeps_ub_none(
    tmp_path: Path, square_instance: TSPInstance
) -> None:
    serializer = BnBSerializer(square_instance, output_root=tmp_path)
    fractions = [1.0, 0.0, 1.0, 0.5, 0.5, 0.0]
    node = _make_node(square_instance, fractions, status=NodeStatus.PRUNED)

    processed = _make_node(
        square_instance, fractions, status=NodeStatus.BRANCHED, node_id=7
    )
    serializer.on_new_node_in_tree(processed, iteration=1)
    serializer.on_node_processed(processed, lb=4.0, ub=426.0, iteration=4)

    serializer.on_new_node_in_tree(node, iteration=1)
    serializer.on_node_global_pruned(node, iteration=5, lb=7.5)  # incumbent omitted

    data = serializer._node_data[node.node_id]
    assert data.ub is None, "no incumbent at prune time means ub stays None"
    assert data.lb == 7.5, "the queue-wide bound is still recorded"
    assert data.pruned_at == 5, "iteration is still recorded"


# --- Integration tests (HiGHS) -------------------------------------------------


def test_process_node_records_branched_edge(
    tmp_path: Path, square_instance: TSPInstance
) -> None:
    """`TSPBnb._process_node` records the edge it branched on.

    Drives `_process_node` directly with a hand-made fractional root: the
    branching strategy picks the edge (all fractions tie at 0.5, so greatest
    weight 1.5 wins, lowest index breaks the remaining tie), two children are
    created (their LPs are solved with HiGHS), and the parent records the
    branched edge index. No queue processing needed.
    """
    serializer = BnBSerializer(square_instance, output_root=tmp_path)
    bnb = _make_bnb(square_instance, serializer)
    node = _make_node(square_instance, [0.5] * 6, node_id=0, parent_id=None)
    serializer.on_new_node_in_tree(node, iteration=1)

    status = bnb._process_node(node)

    assert status is NodeStatus.BRANCHED, "fractional node with no incumbent branches"
    assert node.branched_edge == 2, (
        "most-fractional tie -> greatest weight (1.5) -> lowest index = edge 2 "
        "(adjacency order (0,1),(0,3),(0,2),... puts weight 1.5 at indices 2 and 4)"
    )
    assert len(bnb.node_queue) == 2, "branching enqueues exactly two children"
    assert all(child.status is None for child in bnb.node_queue.nodes_in_queue()), (
        "freshly created children have no status yet"
    )


@pytest.mark.slow
def test_square_best_bound_run_exports_root_outcome(
    tmp_path: Path, square_instance: TSPInstance
) -> None:
    serializer = BnBSerializer(square_instance, output_root=tmp_path)
    bnb = _make_bnb(square_instance, serializer, priority=best_bound_order)
    bnb.search(iteration_limit=100)
    run_dir = bnb.save(open_browser=False)

    data = BnBRunData.model_validate_json(
        (run_dir / "bnb_state.json").read_text(encoding="utf-8")
    )
    # The square's degree-only LP is the integral perimeter tour (4.0) and the
    # NN + 2-opt warm start also finds 4.0, so the root is either Integer or
    # immediately bound-pruned — both are legitimate outcomes.
    assert data.tree.status in (NodeStatus.INTEGER, NodeStatus.PRUNED), (
        f"square root should end Integer or Pruned, got {data.tree.status}"
    )
    if data.tree.status is NodeStatus.PRUNED:
        assert data.tree.prune_reason is PruneReason.NODE_BOUND, (
            "a processed prune is a node-bound prune"
        )
        assert data.tree.pruned_at == data.tree.processed_at, (
            "node-bound prune happens at processing"
        )
        assert data.tree.ub == pytest.approx(4.0), "ub is the warm-start incumbent"
    assert data.solver_config.search_policy == "best_bound_order", (
        "solver_config must record the queue policy"
    )
    assert data.solver_config.search_policy_label == "Best-bound", (
        "solver_config must record the policy label"
    )
    assert data.solver_config.search_policy_description, (
        "policy description must be non-empty"
    )
    assert data.solver_config.branching_strategy == "MostFractionalBranchingStrategy", (
        "solver_config must record the branching strategy class"
    )
    assert data.solver_config.branching_strategy_label == "Most-fractional branching", (
        "solver_config must record the branching strategy label"
    )
    assert data.solver_config.root_heuristics_description, (
        "root heuristic description must be non-empty"
    )


@pytest.mark.slow
def test_dfs_run_exports_prune_reasons(
    tmp_path: Path, square4_instance: TSPInstance
) -> None:
    serializer = BnBSerializer(square4_instance, output_root=tmp_path)
    bnb = _make_bnb(square4_instance, serializer, priority=depth_first_order)
    bnb.search(iteration_limit=100)
    run_dir = bnb.save(open_browser=False)

    data = BnBRunData.model_validate_json(
        (run_dir / "bnb_state.json").read_text(encoding="utf-8")
    )
    nodes = _flatten(data.tree)

    assert data.solver_config.search_policy == "depth_first_order", (
        "solver_config must record the DFS policy"
    )
    assert data.solver_config.search_policy_label == "Depth-first", (
        "solver_config must record the DFS policy label"
    )
    for node in nodes:
        if node.status is NodeStatus.PRUNED:
            assert node.prune_reason in (
                PruneReason.NODE_BOUND,
                PruneReason.GLOBAL_BOUND,
            ), f"pruned node {node.node_id} must record why it was pruned"
            assert node.pruned_at is not None, (
                f"pruned node {node.node_id} must record when it was pruned"
            )
            if node.prune_reason is PruneReason.NODE_BOUND:
                assert node.pruned_at == node.processed_at, (
                    f"node-bound prune {node.node_id} happens at processing"
                )
            if node.prune_reason is PruneReason.GLOBAL_BOUND:
                assert node.lb == pytest.approx(data.iterations[-1].global_lb), (
                    f"leftover {node.node_id} dies against the queue-wide bound "
                    "that closed the queue — the final entry's global_lb"
                )
        if node.status is NodeStatus.INFEASIBLE:
            assert node.infeasible_reason in (
                InfeasibleReason.LP_INFEASIBLE,
                InfeasibleReason.SUBTOURS,
            ), f"infeasible node {node.node_id} must record why"
        if node.status is NodeStatus.BRANCHED:
            assert node.branched_edge is not None, (
                f"branched node {node.node_id} must record its branch edge"
            )
