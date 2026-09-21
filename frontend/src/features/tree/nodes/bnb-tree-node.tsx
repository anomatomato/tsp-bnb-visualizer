import type { BnBFlowNode } from "@/lib/bnb"
import type { NodeStatus } from "@/types/api-types"
import { Handle, NodeToolbar, Position, type NodeProps } from "@xyflow/react"
import type { CSSProperties } from "react"
import { useState } from "react"

const statusClasses: Record<NodeStatus, string> = {
  Feasible: "bg-bnb-status-feasible/20 border-bnb-status-feasible",
  Infeasible: "bg-bnb-status-infeasible/20 border-bnb-status-infeasible",
  Branched: "bg-bnb-status-branched/20 border-bnb-status-branched",
  Pruned: "bg-bnb-status-pruned/20 border-bnb-status-pruned",
  Enqueued: "bg-bnb-status-enqueued/20 border-bnb-status-enqueued",
  Unknown: "bg-muted/20 border-muted-foreground",
}

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
    <>
      <NodeToolbar isVisible={tooltipVisible} position={Position.Top}>
        <button>delete</button>
        <button>copy</button>
        <button>expand</button>
      </NodeToolbar>
      <div
        className={`flex h-12 w-12 place-content-center rounded-full text-xs text-foreground select-none ${statusClasses[node.status]}`}
        title={`#${node.node_id} · ${node.status}`}
        // className="react-flow__node-default"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {node.lb !== null && node.lb !== undefined ? node.lb.toFixed(1) : "-"}
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
    </>
  )
}
