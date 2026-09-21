import type { BnBRunData, NodeVisData } from "@/types/api-types"
import type { Edge, Node } from "@xyflow/react"

export type BnBNodeData = {
  node: Omit<NodeVisData, "children"> // full detail, children stripped (flattened structure)
}

export type BnBFlowNode = Node<BnBNodeData, "bnb">

/** recursive tree -> flat list of (node, parentId), DFS order */
export function flattenTree(
  node: NodeVisData,
  parentId: number | null = null,
  acc: Array<{ node: NodeVisData; parentId: number | null }> = []
): Array<{ node: NodeVisData; parentId: number | null }> {
  acc.push({ node, parentId })
  for (const child of node.children ?? []) {
    flattenTree(child, child.parent_id, acc)
  }
  return acc
}

export function toReactFlow(run: BnBRunData): {
  nodes: BnBFlowNode[]
  edges: Edge[]
} {
  const flat = flattenTree(run.tree)
  const nodes: BnBFlowNode[] = flat.map(({ node }) => {
    const { children: _children, ...rest } = node
    return {
      id: String(node.node_id),
      type: "bnb",
      position: { x: 0, y: 0 }, // dagre fills this
      data: { node: rest },
    }
  })

  const edges: Edge[] = flat
    .filter(({ parentId }) => parentId !== null)
    .map(({ node, parentId }) => {
      return {
        id: `e${parentId}-${node.node_id}`,
        source: String(parentId),
        target: String(node.node_id),
      }
    })

  return { nodes, edges }
}
