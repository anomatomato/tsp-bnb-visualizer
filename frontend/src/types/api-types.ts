/* tslint:disable */

/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Why a node was pruned.
 */
export type PruneReason = "node_bound" | "global_bound"
/**
 * Why a node is infeasible.
 */
export type InfeasibleReason = "lp_infeasible" | "subtours"
/**
 * Enumeration of possible states for a BnB node.
 */
export type NodeStatus = "Integer" | "Infeasible" | "Pruned" | "Branched"

/**
 * One entry in the global best-solutions timeline.
 */
export interface BestSolutionEntry {
  iteration: number
  cost: number
  edge_selection: number[]
  /**
   * Rendered SVG reference for the best tour.
   */
  image_path: string | null
}
/**
 * Top-level JSON structure written to bnb_state.json.
 */
export interface BnBRunData {
  instance: InstanceData
  tree: NodeVisData
  best_solutions: BestSolutionEntry[]
  iterations: IterationEntry[]
  processing_order: number[]
  /**
   * Wall-clock run start, tz-aware ISO 8601. New runs set it; runs exported before the field existed have None (catalog falls back to the run-id timestamp).
   */
  started_at?: string | null
  solver_config: SolverConfigData
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
   * Queue-wide global lower bound (min LP bound over open nodes) when this node's fate was decided: at the iteration it was processed, or the queue-wide bound that closed the queue for globally pruned leftovers. NOT this node's own bound — that is relaxed_solution.objective. None for nodes never decided.
   */
  lb: number | null
  /**
   * Incumbent (best tour cost so far) when this node's fate was decided: at processing for processed nodes, at the prune iteration for globally pruned queue leftovers. None if no incumbent existed.
   */
  ub: number | null
  /**
   * Iteration of the prune decision. Equals processed_at for per-node prunes; the global-prune iteration for queue leftovers.
   */
  pruned_at: number | null
  /**
   * Why pruned.
   */
  prune_reason: PruneReason | null
  /**
   * Why infeasible.
   */
  infeasible_reason: InfeasibleReason | null
  /**
   * Edge index this node branched on (status Branched only).
   */
  branched_edge: number | null
  depth: number
  /**
   * The iteration when the node was created.
   */
  created_at: number
  /**
   * The iteration when the node was processed. This may be later than its creation time. It may also be None if it got pruned.
   */
  processed_at: number | null
  /**
   * Status of the node in the visualization. None until the node reaches a terminal state.
   */
  status: NodeStatus | null
  /**
   * LP relaxation snapshot at the node, if one was rendered.
   */
  relaxed_solution: RelaxedSnapshot | null
  /**
   * Feasible tour snapshot from the heuristic, if one was found.
   */
  heuristic_solution: TourSnapshot | null
  /**
   * Per-edge branching state: None = free, 0 = fixed out, 1 = fixed in. Enables frontend tooltips showing why x_ij is 0/1 (LP choice vs branching fixation)
   */
  fixed_edges: (0 | 1 | null)[]
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
  /**
   * Rendered SVG reference for the relaxation.
   */
  image_path: string | null
}
/**
 * A feasible tour: raw data + rendered SVG reference.
 */
export interface TourSnapshot {
  edge_selection: number[]
  cost: number
  /**
   * Rendered SVG reference for the tour.
   */
  image_path: string | null
}
/**
 * Search state after one iteration
 */
export interface IterationEntry {
  /**
   * The node processed this iteration
   */
  node_id: number
  /**
   * Queue-wide lower bound after the iteration; None = queue empty
   */
  global_lb: number | null
  /**
   * Node lower bound from its relaxation. None for an LP-infeasible processed node
   */
  node_lb: number | null
  /**
   * Best known tour cost after the iteration
   */
  incumbent: number | null
  /**
   * Leftovers globally pruned at this iteration. Normally empty; the final iteration carries the whole remaining queue.
   */
  global_pruned_node_ids?: number[]
}
/**
 * Strategy components used for the BnB run.
 */
export interface SolverConfigData {
  /**
   * OpenNodeQueue policy identifier, e.g. `best_bound_order`
   */
  search_policy: string
  /**
   * Short human-readable policy name for header display
   */
  search_policy_label: string
  /**
   * One-sentence policy description for tooltips
   */
  search_policy_description: string
  /**
   * Branching strategy class name, e.g. `MostFractionalBranchingStrategy`
   */
  branching_strategy: string
  /**
   * Short human-readable branching strategy name
   */
  branching_strategy_label: string
  /**
   * One-sentence branching strategy description
   */
  branching_strategy_description: string
  /**
   * Relaxation solver class name, e.g. `LPRelaxation`
   */
  relaxation: string
  /**
   * Short human-readable relaxation name
   */
  relaxation_label: string
  /**
   * One-sentence relaxation description
   */
  relaxation_description: string
  /**
   * Root heuristic class name, e.g. `TwoOptImproved`
   */
  root_heuristics: string
  /**
   * Short human-readable root heuristic name
   */
  root_heuristics_label: string
  /**
   * One-sentence root heuristic description
   */
  root_heuristics_description: string
}
/**
 * Which strategy components produced this run (identifier + display tiers).
 */
export interface SolverConfigData1 {
  /**
   * OpenNodeQueue policy identifier, e.g. `best_bound_order`
   */
  search_policy: string
  /**
   * Short human-readable policy name for header display
   */
  search_policy_label: string
  /**
   * One-sentence policy description for tooltips
   */
  search_policy_description: string
  /**
   * Branching strategy class name, e.g. `MostFractionalBranchingStrategy`
   */
  branching_strategy: string
  /**
   * Short human-readable branching strategy name
   */
  branching_strategy_label: string
  /**
   * One-sentence branching strategy description
   */
  branching_strategy_description: string
  /**
   * Relaxation solver class name, e.g. `LPRelaxation`
   */
  relaxation: string
  /**
   * Short human-readable relaxation name
   */
  relaxation_label: string
  /**
   * One-sentence relaxation description
   */
  relaxation_description: string
  /**
   * Root heuristic class name, e.g. `TwoOptImproved`
   */
  root_heuristics: string
  /**
   * Short human-readable root heuristic name
   */
  root_heuristics_label: string
  /**
   * One-sentence root heuristic description
   */
  root_heuristics_description: string
}
