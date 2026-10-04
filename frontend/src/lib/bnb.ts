import type { BnBRunData, NodeVisData } from "@/types/api-types"
import type { Edge, Node } from "@xyflow/react"

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

export function incumbentAt(run: BnBRunData, iteration: number) {
  return (
    run.best_solutions.filter((s) => s.iteration <= iteration).at(-1) ?? null
  )
}
