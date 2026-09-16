import type { Edge, NodeTypes } from "@xyflow/react"
import { RoundNode, type RoundNodeType } from "./RoundNode"

export const initialNodes: RoundNodeType[] = [
  {
    id: "n1",
    position: { x: 0, y: 0 },
    data: { label: "Node 1" },
    type: "round",
  },
  {
    id: "n2",
    position: { x: 100, y: 100 },
    data: { label: "Node 2" },
    type: "round",
  },
]

export const initialEdges: Edge[] = [
  {
    id: "e1-2",
    source: "n1",
    target: "n2",
    type: "bezier",
    label: "connects with",
  },
]

export const nodeTypes = {
  round: RoundNode,
} as const satisfies NodeTypes
