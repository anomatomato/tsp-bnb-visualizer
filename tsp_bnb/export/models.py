"""Pydantic models for BnB state JSON export."""

from pydantic import BaseModel, Field

from ..bnb_nodes import InfeasibleReason, NodeStatus, PruneReason


class NodePosition(BaseModel):
    """A node's fixed position for rendering."""

    id: int
    x: float
    y: float


class EdgeData(BaseModel):
    """An edge in the TSP instance."""

    u: int
    v: int
    weight: float


class InstanceData(BaseModel):
    """Serialized TSP instance with fixed node positions."""

    name: str
    nodes: list[NodePosition]
    edges: list[EdgeData]


class RelaxedSnapshot(BaseModel):
    """LP relaxation at a node: raw data + rendered SVG reference."""

    edge_fractions: list[float]
    objective: float
    is_integral_tour: bool
    image_path: str | None = Field(
        ..., description="Rendered SVG reference for the relaxation."
    )


class TourSnapshot(BaseModel):
    """A feasible tour: raw data + rendered SVG reference."""

    edge_selection: list[int]
    cost: float
    image_path: str | None = Field(
        ..., description="Rendered SVG reference for the tour."
    )


class NodeVisData(BaseModel):
    """A node in the exported BnB tree (recursive)."""

    node_id: int = Field(..., description="The ID of the root node.")
    parent_id: int | None = Field(..., description="The ID of the parent node.")
    lb: float | None = Field(
        ...,
        description=(
            "Queue-wide global lower bound (min LP bound over open nodes) when "
            "this node's fate was decided: at the iteration it was processed, "
            "or the queue-wide bound that closed the queue for globally pruned "
            "leftovers. NOT this node's own bound — that is "
            "relaxed_solution.objective. None for nodes never decided."
        ),
    )
    ub: float | None = Field(
        ...,
        description=(
            "Incumbent (best tour cost so far) when this node's fate was decided: "
            "at processing for processed nodes, at the prune iteration for "
            "globally pruned queue leftovers. None if no incumbent existed."
        ),
    )
    pruned_at: int | None = Field(
        ...,
        description="Iteration of the prune decision. Equals processed_at for per-node prunes; the global-prune iteration for queue leftovers.",
    )
    prune_reason: PruneReason | None = Field(..., description="Why pruned.")
    infeasible_reason: InfeasibleReason | None = Field(
        ..., description="Why infeasible."
    )
    branched_edge: int | None = Field(
        ...,
        description="Edge index this node branched on (status Branched only).",
    )
    depth: int
    created_at: int = Field(..., description="The iteration when the node was created.")
    processed_at: int | None = Field(
        ...,
        description="The iteration when the node was processed. This may be later than its creation time. It may also be None if it got pruned.",
    )
    status: NodeStatus | None = Field(
        ...,
        description="Status of the node in the visualization. None until the node reaches a terminal state.",
    )
    relaxed_solution: RelaxedSnapshot | None = Field(
        ..., description="LP relaxation snapshot at the node, if one was rendered."
    )
    heuristic_solution: TourSnapshot | None = Field(
        ..., description="Feasible tour snapshot from the heuristic, if one was found."
    )
    fixed_edges: list[int | None] = Field(
        ...,
        description="Per-edge branching state: None = free, 0 = fixed out, 1 = fixed in. Enables frontend tooltips showing why x_ij is 0/1 (LP choice vs branching fixation)",
    )
    children: list["NodeVisData"] = Field(..., description="Children of the node.")


class BestSolutionEntry(BaseModel):
    """One entry in the global best-solutions timeline."""

    iteration: int
    cost: float
    edge_selection: list[int]
    image_path: str | None = Field(
        ..., description="Rendered SVG reference for the best tour."
    )


class IterationEntry(BaseModel):
    """Search state after one iteration"""

    node_id: int = Field(..., description="The node processed this iteration")
    global_lb: float | None = Field(
        ...,
        description="Queue-wide lower bound after the iteration; None = queue empty",
    )
    node_lb: float | None = Field(
        ...,
        description="Node lower bound from its relaxation. None for an LP-infeasible processed node",
    )
    incumbent: float | None = Field(
        ..., description="Best known tour cost after the iteration"
    )
    global_pruned_node_ids: list[int] = Field(
        default_factory=list,
        description="Leftovers globally pruned at this iteration. Normally empty; the final iteration carries the whole remaining queue.",
    )


class SolverConfigData(BaseModel):
    """Which strategy components produced this run (identifier + display tiers)."""

    search_policy: str = Field(
        ..., description="OpenNodeQueue policy identifier, e.g. `best_bound_order`"
    )
    search_policy_label: str = Field(
        ..., description="Short human-readable policy name for header display"
    )
    search_policy_description: str = Field(
        ..., description="One-sentence policy description for tooltips"
    )
    branching_strategy: str = Field(
        ...,
        description="Branching strategy class name, e.g. `MostFractionalBranchingStrategy`",
    )
    branching_strategy_label: str = Field(
        ..., description="Short human-readable branching strategy name"
    )
    branching_strategy_description: str = Field(
        ..., description="One-sentence branching strategy description"
    )
    relaxation: str = Field(
        ..., description="Relaxation solver class name, e.g. `LPRelaxation`"
    )
    relaxation_label: str = Field(
        ..., description="Short human-readable relaxation name"
    )
    relaxation_description: str = Field(
        ..., description="One-sentence relaxation description"
    )
    root_heuristics: str = Field(
        ..., description="Root heuristic class name, e.g. `TwoOptImproved`"
    )
    root_heuristics_label: str = Field(
        ..., description="Short human-readable root heuristic name"
    )
    root_heuristics_description: str = Field(
        ..., description="One-sentence root heuristic description"
    )


class BnBRunData(BaseModel):
    """Top-level JSON structure written to bnb_state.json."""

    instance: InstanceData
    tree: NodeVisData
    best_solutions: list[BestSolutionEntry]
    iterations: list[IterationEntry]
    processing_order: list[int]
    started_at: str | None = Field(
        default=None,
        description=(
            "Wall-clock run start, tz-aware ISO 8601. New runs set it; runs "
            "exported before the field existed have None (catalog falls back "
            "to the run-id timestamp)."
        ),
    )
    solver_config: SolverConfigData = Field(
        ..., description="Strategy components used for the BnB run."
    )
