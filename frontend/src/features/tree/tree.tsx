import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"
import { toReactFlow, type BnBFlowNode } from "@/lib/bnb"
import { layoutTree } from "@/lib/layout"
import runJson from "@/mock/eil51/bnb_state.json"
import type { BnBRunData } from "@/types/api-types"
import {
  Background,
  ControlButton,
  Controls,
  MiniMap,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useReactFlow,
  type MiniMapNodeProps,
} from "@xyflow/react"
import { ArrowDownUp, ArrowLeftRight } from "lucide-react"
import { useCallback, useMemo, useState } from "react"
import { nodeTypes } from "./nodes"

interface BnBTreeProps {
  iteration: number
}

// tsc infers JSON string fields as `string`, not the generated literal
// unions — one typed cast at the boundary keeps toReactFlow type-safe.
const run = runJson as BnBRunData
const { nodes: initialNodes, edges: initialEdges } = toReactFlow(run)
// layouts are pure functions of the static mock — precompute both once,
// toggling direction is then a zero-cost array swap
const layouts = {
  TB: layoutTree(initialNodes, initialEdges, "TB"),
  LR: layoutTree(initialNodes, initialEdges, "LR"),
} as const

export function BnBTree({ iteration }: BnBTreeProps) {
  return (
    <ReactFlowProvider>
      <BnBTreeCanvas iteration={iteration} />
    </ReactFlowProvider>
  )
}

function BnBTreeCanvas({ iteration }: BnBTreeProps) {
  const { theme } = useTheme()
  const [nodes, setNodes, onNodesChange] = useNodesState(layouts.TB)
  const [direction, setDirection] = useState<"LR" | "TB">("TB")
  const { fitView } = useReactFlow<BnBFlowNode>()

  const finalNodes: BnBFlowNode[] = useMemo(() => {
    const returnValue = nodes.map((n) => {
      const processed_at = n.data.node.processed_at
      const is_processed =
        processed_at !== null &&
        processed_at !== undefined &&
        processed_at <= iteration
      return {
        ...n,
        data: {
          ...n.data,
          dimmed: !is_processed,
        },
      }
    })
    return returnValue
  }, [nodes, iteration])

  const onToggleLayout = useCallback(() => {
    const next = direction === "TB" ? "LR" : "TB"
    setDirection(next)
    setNodes(layouts[next])
    requestAnimationFrame(() => fitView({ duration: 0 }))
  }, [direction, setNodes, fitView])

  return (
    <ReactFlow
      nodes={finalNodes}
      edges={initialEdges}
      onNodesChange={onNodesChange}
      nodeTypes={nodeTypes}
      colorMode={theme}
      nodesDraggable={false}
      minZoom={0.1}
      fitView
    >
      <MiniMap nodeComponent={MiniMapNode} pannable zoomable />
      <Background />
      <Controls showInteractive={false}>
        <ControlButton onClick={onToggleLayout} title="Change Layout">
          {direction === "TB" ? <ArrowLeftRight /> : <ArrowDownUp />}
        </ControlButton>
      </Controls>
      <Panel position="top-right">
        {/* label/icon shows the direction you will switch TO */}
        <Button
          variant="outline"
          onClick={onToggleLayout}
          title="Change Layout"
        >
          {direction === "TB" ? <ArrowLeftRight /> : <ArrowDownUp />}
          {direction === "TB" ? "horizontal" : "vertical"}
        </Button>
      </Panel>
    </ReactFlow>
  )
}

function MiniMapNode({ x, y }: MiniMapNodeProps) {
  return <circle cx={x} cy={y} r="30" className="fill-pink-500 opacity-50" />
}
