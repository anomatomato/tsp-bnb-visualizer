import type { BnBFlowNode } from "@/lib/bnb"
import { Handle, NodeToolbar, Position, type NodeProps } from "@xyflow/react"
import type { CSSProperties } from "react"
import { useEffect, useRef, useState } from "react"
import { statusNodeClass, statusCurrentNodeClass } from "@/lib/status"
import { cn } from "cn"
import { ArrowDownCircle, ArrowUpCircle } from "lucide-react"
import { useIterationContext } from "@/context/iteration-context"
import { useDirectionContext } from "../context/direction-context"
import type { Direction } from "@/lib/layout"

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

const toolbarTimeout = 100

const labelPositionClass: Record<Direction, string> = {
  TB: "-top-3.5 -left-1",
  LR: "-top-2 -left-3",
}

export function BnBTreeNode({
  selected,
  data,
  targetPosition,
  sourcePosition,
}: NodeProps<BnBFlowNode>) {
  // 1. hooks
  const { iteration, setIteration } = useIterationContext()
  const { direction } = useDirectionContext()
  const [hovered, setHovered] = useState(false)
  const timeoutId = useRef<number | null>(null)
  // Disposal of timeout on unmount
  useEffect(
    () => () => {
      if (timeoutId.current) clearTimeout(timeoutId.current)
    },
    []
  )

  // 2. derived
  const tooltipVisible = selected || hovered
  const { node } = data
  const objective = node.relaxed_solution?.objective
  const label = objective === undefined ? "-" : objective.toFixed(1)

  const processed_at = data.node.processed_at
  const isProcessed = processed_at !== null && processed_at <= iteration
  const isCurrent = processed_at === iteration

  // 3. handlers
  function handleMouseEnter() {
    if (timeoutId.current) {
      clearTimeout(timeoutId.current)
    }
    setHovered(true)
  }

  function handleMouseLeave() {
    if (timeoutId.current) {
      clearTimeout(timeoutId.current)
    }
    timeoutId.current = setTimeout(() => setHovered(false), toolbarTimeout)
  }

  function handleNodeClick() {
    if (node.processed_at !== null) {
      setIteration(node.processed_at)
    }
  }

  return (
    <div onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
      <NodeToolbar isVisible={tooltipVisible} position={Position.Top}>
        <div className="flex flex-col gap-1 rounded-md border bg-accent px-2 py-1 text-sm">
          <span className="flex items-center">
            <ArrowDownCircle size="16" className="mr-2" /> LB:{" "}
            {node.relaxed_solution?.objective.toFixed(2)}
          </span>
          <span className="flex items-center">
            <ArrowUpCircle size="16" className="mr-2" /> UB: {node.ub}
          </span>
        </div>
      </NodeToolbar>
      {/*<EdgeToolbar>testing</EdgeToolbar>*/}
      <button
        onClick={handleNodeClick}
        className={cn(
          "relative flex size-12 flex-col place-content-center items-center rounded-full text-foreground",
          statusNodeClass(node.status),
          !isProcessed && "opacity-30",
          isCurrent && [
            "shadow-[0_0_--spacing(6)_(--tw-shadow-color)]",
            statusCurrentNodeClass(node.status),
          ]
        )}
        // title={`#${node.node_id} · ${node.status}`}
        // className="react-flow__node-default"
      >
        {/*<span className="font-bold">{node.processed_at ?? "-"}</span>*/}
        <span
          className={
            // Auto-fit label: shrink the font until the number fits inside the node circle; never grow past the normal size. Expanded formula:
            //   font-size = min(1rem, 44px / (n × 0.62em))
            // · --spacing(11) = 11 × 4px = 44px — the usable width inside the
            //   size-12 (48px) circle, kept in grid units so it tracks --spacing.
            // · var(--n) is the label's character count, set in the style prop
            //   below — inline because it changes per render; Tailwind only
            //   emits classes it finds as complete literal text.
            // · tabular-nums gives every digit the same advance width, so
            //   n glyphs occupy n × 0.62em; 44px ÷ that = the px-per-em
            //   (i.e. font-size) that makes the run exactly fill the circle.
            // · 0.62 is the measured per-glyph em width of this font
            "text-[min(1rem,calc((--spacing(11.5))/(var(--n)*0.62)))] font-semibold tabular-nums"
          }
          style={
            {
              "--n": label.length,
            } as CSSProperties
          }
        >
          {label}
        </span>
        <span
          className={cn(
            "absolute -top-3.5 -left-1 text-xs text-muted-foreground tabular-nums",
            labelPositionClass[direction]
          )}
        >
          {node.processed_at}
        </span>
      </button>
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
