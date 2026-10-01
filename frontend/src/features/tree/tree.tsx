import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"
import { toReactFlow, type BnBFlowNode } from "@/lib/bnb"
import { layoutTree, type Direction } from "@/lib/layout"
import runJson from "@/mock/eil51/bnb_state.json"
import type { BnBRunData, NodeStatus } from "@/types/api-types"
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
import { type Dispatch, type SetStateAction } from "react"
import { nodeTypes } from "./nodes"
import { statusNodeClasses } from "@/lib/status"
import { Card, CardContent } from "@/components/ui/card"
import { TimeLine } from "./components/timeline"

interface BnBTreeProps {
  iteration: number
  max: number
  setIteration: Dispatch<SetStateAction<number>>
}

// tsc infers JSON string fields as `string`, not the generated literal
// unions — one typed cast at the boundary keeps toReactFlow type-safe.
const run = runJson as BnBRunData
const { nodes: initialNodes, edges: initialEdges } = toReactFlow(run)
// layouts are pure functions of the static mock — precompute both once,
// toggling direction is then a zero-cost array swap
const layouts = {
  TB: layoutTree(initialNodes, initialEdges, "TB", 30, 42),
  LR: layoutTree(initialNodes, initialEdges, "LR", 8, 96),
} as const

const statuses = Object.keys(statusNodeClasses) as NodeStatus[]

export function BnBTree(props: BnBTreeProps) {
  return (
    <ReactFlowProvider>
      <BnBTreeCanvas {...props} />
    </ReactFlowProvider>
  )
}

function BnBTreeCanvas({ iteration, setIteration, max }: BnBTreeProps) {
  const { theme } = useTheme()
  const [nodes, setNodes, onNodesChange] = useNodesState(layouts.TB)
  const [direction, setDirection] = useState<Direction>("TB")
  const { fitView } = useReactFlow<BnBFlowNode>()

  const finalNodes: BnBFlowNode[] = useMemo(() => {
    const returnValue = nodes.map((n) => {
      const processed_at = n.data.node.processed_at
      const is_processed = processed_at !== null && processed_at <= iteration
      const current = processed_at === iteration
      return {
        ...n,
        data: {
          ...n.data,
          dimmed: !is_processed,
          current: current,
        },
      }
    })
    return returnValue
  }, [nodes, iteration])

  const handleToggleLayout = useCallback(() => {
    const next: Direction = direction === "TB" ? "LR" : "TB"
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
        <ControlButton onClick={handleToggleLayout} title="Change Layout">
          {direction === "TB" ? <ArrowLeftRight /> : <ArrowDownUp />}
        </ControlButton>
      </Controls>
      <Panel position="top-left">
        <Card>
          <CardContent>
            <ul>
              {statuses.map((status) => (
                <li key={status} className="flex items-center gap-2">
                  <span
                    className={`size-3 rounded-full ${statusNodeClasses[status]}`}
                  ></span>
                  <span>{status}</span>
                </li>
              ))}
            </ul>
            <p className="text-muted-foreground">label: LP bound</p>
          </CardContent>
        </Card>
      </Panel>
      <Panel position="top-right">
        {/* label/icon shows the direction you will switch TO */}
        <Button
          variant="outline"
          onClick={handleToggleLayout}
          title="Change Layout"
        >
          {direction === "TB" ? <ArrowLeftRight /> : <ArrowDownUp />}
          {direction === "TB" ? "horizontal" : "vertical"}
        </Button>
      </Panel>
      <Panel position="bottom-center">
        <TimeLine iteration={iteration} setIteration={setIteration} max={max} />
      </Panel>
    </ReactFlow>
  )
}

function MiniMapNode({ x, y }: MiniMapNodeProps) {
  return (
    <circle
      cx={x}
      cy={y}
      r="30"
      className="fill-pink-500 opacity-50 dark:fill-pink-400"
    />
  )
}
