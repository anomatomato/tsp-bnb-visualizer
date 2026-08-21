"""Pydantic models for BnB state JSON export."""

from pydantic import BaseModel, Field

from ..bnb_nodes import NodeStatus


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
    image_path: str | None = Field(default=None)


class TourSnapshot(BaseModel):
    """A feasible tour: raw data + rendered SVG reference."""

    edge_selection: list[int]
    cost: float
    image_path: str | None = Field(default=None)


class NodeVisData(BaseModel):
    """A node in the exported BnB tree (recursive)."""

    node_id: int = Field(..., description="The ID of the root node.")
    parent_id: int | None = Field(..., description="The ID of the parent node.")
    lb: float | None = Field(
        default=None,
        description="The lower bound from the relaxed solution. May also be None if it got pruned.",
    )
    ub: float | None = Field(
        default=None,
        description="The upper bound of the node from the heuristic solution. May also be None if there is no heuristic solution or it got pruned.",
    )
    depth: int = 0
    created_at: int = Field(..., description="The iteration when the node was created.")
    processed_at: int | None = Field(
        default=None,
        description="The iteration when the node was processed. This may be later than its creation time. It may also be None if it got pruned.",
    )
    status: NodeStatus = Field(
        ..., description="Status of the node in the visualization."
    )
    relaxed_solution: RelaxedSnapshot | None = Field(default=None)
    heuristic_solution: TourSnapshot | None = Field(default=None)
    fixed_edges: list[int | None] | None = Field(
        default=None,
        description="Per-edge branching state: None = free, 0 = fixed out, 1 = fixed in. Enables frontend tooltips showing why x_ij is 0/1 (LP choice vs branching fixation)",
    )
    children: list["NodeVisData"] = Field(
        default_factory=list, description="Children of the node."
    )


class BestSolutionEntry(BaseModel):
    """One entry in the global best-solutions timeline."""

    iteration: int
    cost: float
    edge_selection: list[int]
    image_path: str | None = Field(default=None)


class BnBRunData(BaseModel):
    """Top-level JSON structure written to bnb_state.json."""

    instance: InstanceData
    tree: NodeVisData
    best_solutions: list[BestSolutionEntry]
    processing_order: list[int]
