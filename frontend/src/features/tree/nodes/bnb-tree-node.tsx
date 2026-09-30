import type { BnBFlowNode } from "@/lib/bnb"
import { Handle, NodeToolbar, Position, type NodeProps } from "@xyflow/react"
import type { CSSProperties } from "react"
import { useState } from "react"
import { statusNodeClass } from "@/lib/status"

const invisibleHandle = {
  opacity: 0, // Hide handles
  width: 1,
  height: 1,
  minWidth: 1,
  minHeight: 1,
  border: "none",
  background: "none",
  transform: "translate(0,0)",
} as const satisfies CSSProperties

export function BnBTreeNode({
  selected,
  data,
  targetPosition,
  sourcePosition,
}: NodeProps<BnBFlowNode>) {
  const [hovered, setHovered] = useState(false)
  const tooltipVisible = selected || hovered
  const { node } = data

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <NodeToolbar isVisible={tooltipVisible} position={Position.Top}>
        {node.lb?.toFixed(1)} - {node.ub} - {node.status ?? "never processed"}
      </NodeToolbar>
      <div
        className={`flex h-12 w-12 flex-col place-content-center items-center gap-0 rounded-full text-[14px] text-foreground ${statusNodeClass(node.status)} ${data.dimmed ? "opacity-30" : ""}`}
        // title={`#${node.node_id} · ${node.status}`}
        // className="react-flow__node-default"
      >
        <span className="font-bold">{node.processed_at ?? "-"}</span>
        <span>{node.relaxed_solution?.objective.toFixed(1) ?? "-"}</span>
      </div>
      {/* Handles stay mounted (edges anchor to them) but invisible */}
      <Handle
        type="target"
        position={targetPosition ?? Position.Left}
        style={invisibleHandle}
      />
      <Handle
        type="source"
        position={sourcePosition ?? Position.Right}
        style={invisibleHandle}
      />
    </div>
  )
}
