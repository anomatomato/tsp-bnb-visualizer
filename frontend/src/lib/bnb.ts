import type {
  BestSolutionEntry,
  BnBRunData,
  EdgeData,
  NodeVisData,
} from "@/types/api-types"
import type { Edge, Node } from "@xyflow/react"

const FRACTION_TOL = 1e-6 // same tolerance as in backend

/** a tree node with its recursive `children` stripped - the flat form */
export type FlatNode = Omit<NodeVisData, "children">

export type BnBFlowNodeData = {
  node: FlatNode
}

export type BnBFlowNode = Node<BnBFlowNodeData, "bnb">

/** recursive tree -> flat list of (node, parentId), DFS order */
export function flattenTree(
  node: NodeVisData,
  acc: FlatNode[] = []
): FlatNode[] {
  const { children: _children, ...rest } = node
  acc.push(rest)
  for (const child of node.children ?? []) {
    flattenTree(child, acc)
  }
  return acc
}

export function toReactFlow(run: BnBRunData): {
  nodes: BnBFlowNode[]
  edges: Edge[]
} {
  const flat = flattenTree(run.tree)
  const nodes: BnBFlowNode[] = flat.map((node) => {
    return {
      id: String(node.node_id),
      type: "bnb",
      position: { x: 0, y: 0 }, // dagre fills this
      data: { node },
    }
  })

  const edges: Edge[] = flat
    .filter((node) => node.parent_id !== null)
    .map((node) => {
      return {
        id: `e${node.parent_id}-${node.node_id}`,
        source: String(node.parent_id),
        target: String(node.node_id),
      }
    })

  return { nodes, edges }
}

export function toNodeMap(
  run: BnBRunData
): Map<number, Omit<NodeVisData, "children">> {
  const map = new Map(flattenTree(run.tree).map((node) => [node.node_id, node]))
  return map
}

export function incumbentAt(
  run: BnBRunData,
  iteration: number
): BestSolutionEntry | null {
  return (
    run.best_solutions.filter((s) => s.iteration <= iteration).at(-1) ?? null
  )
}

/** indices where fixed_edges is 1 or 0 (inner null = free edge) */
export function fixedEdgesOf(node: FlatNode): {
  fixedIn: number[]
  fixedOut: number[]
} {
  const fixedIn = node.fixed_edges.filter((e) => e === 1)
  const fixedOut = node.fixed_edges.filter((e) => e === 0)

  return {
    fixedIn,
    fixedOut,
  }
}

/** indices with a strictly fractional LP value (tolerance-checked) */
export function fractionalEdges(node: FlatNode): number[] {
  const fractions = node.relaxed_solution?.edge_fractions
  if (!fractions) return []

  return fractions.flatMap((frac, i) =>
    FRACTION_TOL <= frac && frac <= 1 - FRACTION_TOL ? [i] : []
  )
}

/** the iteration a click should seek to: processed_at ?? pruned_at */
export function decisionIteration(node: FlatNode): number | null {
  return node.processed_at ?? node.pruned_at
}

/** which edge split this node from its parent, and which side it landed on */
export function ownBranch(
  node: FlatNode,
  parent: FlatNode
): { edge: number; side: 0 | 1 } | null {
  const edge = parent.branched_edge
  if (edge === null) return null

  const side = node.fixed_edges[edge]
  if (side !== 0 && side !== 1) return null

  return { edge, side }
}

export function edgeLabel(edges: EdgeData[], index: number): string {
  const e = edges[index]
  if (!e) return `edge ${index}`

  return `(${e.u}-${e.v})`
}

/** outcome explanation sentence */
export function explainOutcome(node: FlatNode, edges: EdgeData[]): string {
  switch (node.status) {
    case "Branched": {
      const i = node.branched_edge
      const label = i === null ? "-" : edgeLabel(edges, i)
      const fraction =
        i === null ? undefined : node.relaxed_solution?.edge_fractions[i]
      return `Branched on edge ${label}: the LP left it at ${fmtFraction(fraction)}`
    }
    case "Integer": {
      return `Integral LP relaxation - one complete tour. It becomes the new incumbent (best tour so far).`
    }
    case "Pruned": {
      switch (node.prune_reason) {
        case "global_bound": {
          return `LP bound ${fmtFraction(node.relaxed_solution?.objective)} ≥ incumbent ${fmtFraction(node.ub)} - Pruned globally at iteration ${node.pruned_at ?? "-"}`
        }
        case "node_bound": {
          return `Pruned at iteration ${node.pruned_at ?? "-"}: its own LP bound ${fmtFraction(node.relaxed_solution?.objective)} was ≥ the incumbent ${fmtFraction(node.ub)} - no better tour can come from this subtree.`
        }
        default: {
          return `Pruned at iteration ${node.pruned_at ?? "-"}`
        }
      }
    }
    case "Infeasible": {
      switch (node.infeasible_reason) {
        case "subtours": {
          return `Infeasible: the LP is integral but forms ≥ 2 disconnected subtours - not a single tour, and no fractional edge is left to branch on.`
        }
        case "lp_infeasible": {
          return `Infeasible: no LP solution exists.`
        }
        default: {
          return `Pruned at iteration ${node.pruned_at ?? "-"}`
        }
      }
    }
    default:
      return `Unknown node status: ${node.status}`
  }
}

function fmtFraction(n: number | null | undefined): string {
  return n?.toFixed(2) ?? "-"
}
