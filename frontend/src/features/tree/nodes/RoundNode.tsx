import {
  Handle,
  NodeToolbar,
  Position,
  type Node,
  type NodeProps,
} from "@xyflow/react"
import type { CSSProperties } from "react"
import { useState } from "react"

type RoundNodeData = { label: string }

export type RoundNodeType = Node<RoundNodeData, "round">

const invisibleHandle: CSSProperties = {
  opacity: 0, // Hide handles
  width: 1,
  height: 1,
  minWidth: 1,
  minHeight: 1,
  border: "none",
  background: "none",
  transform: "translate(0,0)",
}

export function RoundNode({ selected, data }: NodeProps<RoundNodeType>) {
  const [hovered, setHovered] = useState(false)
  const tooltipVisible = selected || hovered

  return (
    <>
      <NodeToolbar isVisible={tooltipVisible} position={Position.Top}>
        <button>delete</button>
        <button>copy</button>
        <button>expand</button>
      </NodeToolbar>
      <div
        style={{
          width: 50,
          height: 50,
          borderRadius: "50%", // ← round
          background: "#7b2ff7",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
          userSelect: "none",
        }}
        // className="react-flow__node-default"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {data.label}
      </div>
      {/* Handles stay mounted (edges anchor to them) but invisible */}
      <Handle type="target" position={Position.Left} style={invisibleHandle} />
      <Handle type="source" position={Position.Right} style={invisibleHandle} />
    </>
  )
}
