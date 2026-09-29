/** see https://reactflow.dev/examples/layout/dagre */

import dagre, {
  type EdgeLabel,
  type GraphLabel,
  type NodeLabel,
} from "@dagrejs/dagre"
import type { Edge, Node } from "@xyflow/react"

const nodeDiameter = 48

export type Direction = "LR" | "TB"

export function layoutTree<N extends Node>(
  nodes: N[],
  edges: Edge[],
  direction: Direction = "TB",
  nodesep: number | undefined = undefined,
  ranksep: number | undefined = undefined
) {
  const g = new dagre.graphlib.Graph<GraphLabel, NodeLabel, EdgeLabel>()

  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: direction, nodesep: nodesep, ranksep: ranksep })

  const isHorizontal = direction === "LR"

  for (const n of nodes) {
    g.setNode(n.id, {
      width: nodeDiameter,
      height: nodeDiameter,
    }) // node size
  }
  for (const e of edges) {
    g.setEdge(e.source, e.target)
  }
  dagre.layout(g)

  const newNodes: N[] = nodes.map((n) => {
    const pos = g.node(n.id) // center coordinates
    const newNode: N = {
      ...n,
      targetPosition: isHorizontal ? "left" : "top",
      sourcePosition: isHorizontal ? "right" : "bottom",
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      position: {
        x: (pos.x ?? nodeDiameter) - nodeDiameter / 2,
        y: (pos.y ?? nodeDiameter) - nodeDiameter / 2,
      },
    }
    return newNode
  })

  return newNodes
}
