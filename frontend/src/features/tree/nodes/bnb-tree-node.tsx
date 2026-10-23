import {
  decisionIteration,
  fixedEdgesOf,
  outcomeHeadline,
  type BnBFlowNode,
} from "@/lib/bnb"
import { Handle, NodeToolbar, Position, type NodeProps } from "@xyflow/react"
import type { CSSProperties } from "react"
import { useEffect, useRef, useState } from "react"
import {
  statusBadgeClass,
  statusCurrentNodeClass,
  statusNodeClass,
} from "@/lib/status"
import { cn } from "cn"
import {
  ArrowDownCircle,
  ArrowUpCircle,
  Globe,
  type LucideIcon,
} from "lucide-react"
import { useIterationContext } from "@/context/iteration-context"
import { useDirectionContext } from "../context/direction-context"
import type { Direction } from "@/lib/layout"
import { useRunContext } from "@/context/run-context"

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

/** one muted icon + label / right-aligned value row of the tooltip stats grid */
function StatRow({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon
  label: string
  value: number | null | undefined
}) {
  return (
    <div className="flex items-center gap-2">
      <dt className="flex items-center gap-2 text-muted-foreground">
        <Icon size={14} className="shrink-0" />
        {label}
      </dt>
      <dd className="ml-auto tabular-nums">{value?.toFixed(2) ?? "–"}</dd>
    </div>
  )
}

export function BnBTreeNode({
  selected,
  data,
  targetPosition,
  sourcePosition,
}: NodeProps<BnBFlowNode>) {
  // 1. hooks
  const { runData } = useRunContext()
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

  const decision = decisionIteration(node)
  const isDecided = decision !== null && decision <= iteration
  const isCurrent = decision === iteration && node.processed_at === iteration
  const isPruned = node.status === "Pruned"
  const { fixedIn, fixedOut } = fixedEdgesOf(node)

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
    if (decision !== null) {
      setIteration(decision)
    }
  }

  return (
    <div onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
      <NodeToolbar isVisible={tooltipVisible} position={Position.Top}>
        {/* summary card: status dot + meta, short headline, bounds grid,
            fixation counts. Full depth lives in the inspector. */}
        <div className="flex max-w-72 flex-col gap-2 rounded-md border bg-accent px-3 py-2 text-sm select-text">
          <h2 className="flex items-center gap-2">
            <span
              className={cn(
                "size-2 shrink-0 rounded-full",
                statusBadgeClass(node.status)
              )}
            />
            <span className="font-semibold">{node.status ?? "Open"}</span>
            <span className="text-xs text-muted-foreground tabular-nums">
              #{decision} · depth {node.depth}
            </span>
          </h2>
          <p className="leading-normal">
            {outcomeHeadline(node, runData.instance.edges)}
          </p>
          <dl className="flex flex-col gap-1">
            <StatRow
              icon={ArrowDownCircle}
              label="LP bound"
              value={node.relaxed_solution?.objective}
            />
            <StatRow icon={ArrowUpCircle} label="Incumbent" value={node.ub} />
            <StatRow icon={Globe} label="GlobalLB" value={node.lb} />
          </dl>
          {fixedIn.length + fixedOut.length > 0 && (
            <p className="text-xs text-muted-foreground tabular-nums">
              {fixedIn.length} fixed in · {fixedOut.length} fixed out
            </p>
          )}
        </div>
      </NodeToolbar>
      {/*<EdgeToolbar>testing</EdgeToolbar>*/}
      <button
        onClick={handleNodeClick}
        className={cn(
          "relative flex size-12 flex-col place-content-center items-center rounded-full text-foreground",
          statusNodeClass(node.status),
          !isDecided && "opacity-30",
          isPruned && isDecided && !isCurrent && "opacity-60",
          isCurrent && [
            "shadow-[0_0_--spacing(6)_(--tw-shadow-color)]",
            statusCurrentNodeClass(node.status),
          ]
        )}
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
