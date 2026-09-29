/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
*/

/**
 * Status of the node in the visualization.
 */
export type NodeStatus = "Feasible" | "Infeasible" | "Pruned" | "Branched"

/**
 * One entry in the global best-solutions timeline.
 */
export interface BestSolutionEntry {
  iteration: number
  cost: number
  edge_selection: number[]
  image_path: string | null
}
/**
 * Top-level JSON structure written to bnb_state.json.
 */
export interface BnBRunData {
  instance: InstanceData
  tree: NodeVisData
  best_solutions: BestSolutionEntry[]
  processing_order: number[]
}
/**
 * Serialized TSP instance with fixed node positions.
 */
export interface InstanceData {
  name: string
  nodes: NodePosition[]
  edges: EdgeData[]
}
/**
 * A node's fixed position for rendering.
 */
export interface NodePosition {
  id: number
  x: number
  y: number
}
/**
 * An edge in the TSP instance.
 */
export interface EdgeData {
  u: number
  v: number
  weight: number
}
/**
 * A node in the exported BnB tree (recursive).
 */
export interface NodeVisData {
  /**
   * The ID of the root node.
   */
  node_id: number
  /**
   * The ID of the parent node.
   */
  parent_id: number | null
  /**
   * The lower bound from the relaxed solution. May also be None if it got pruned.
   */
  lb: number | null
  /**
   * The upper bound of the node from the heuristic solution. May also be None if there is no heuristic solution or it got pruned.
   */
  ub: number | null
  depth: number
  /**
   * The iteration when the node was created.
   */
  created_at: number
  /**
   * The iteration when the node was processed. This may be later than its creation time. It may also be None if it got pruned.
   */
  processed_at: number | null
  status: NodeStatus
  relaxed_solution: RelaxedSnapshot | null
  heuristic_solution: TourSnapshot | null
  /**
   * Per-edge branching state: None = free, 0 = fixed out, 1 = fixed in. Enables frontend tooltips showing why x_ij is 0/1 (LP choice vs branching fixation)
   */
  fixed_edges: (0 | 1 | null)[] | null
  /**
   * Children of the node.
   */
  children: NodeVisData[]
}
/**
 * LP relaxation at a node: raw data + rendered SVG reference.
 */
export interface RelaxedSnapshot {
  edge_fractions: number[]
  objective: number
  is_integral_tour: boolean
  image_path: string | null
}
/**
 * A feasible tour: raw data + rendered SVG reference.
 */
export interface TourSnapshot {
  edge_selection: number[]
  cost: number
  image_path: string | null
}
