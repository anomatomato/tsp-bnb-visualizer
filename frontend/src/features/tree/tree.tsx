import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"
import { toReactFlow, type BnBFlowNode } from "@/lib/bnb"
import { layoutTree, type Direction } from "@/lib/layout"
import {
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
import { ArrowDownUp, ArrowLeftRight, Maximize } from "lucide-react"
import { useCallback, useMemo } from "react"
import { nodeTypes } from "./nodes"
import { TimeLine } from "./components/timeline"
import Legend from "./components/legend"
import {
  DirectionProvider,
  useDirectionContext,
} from "./context/direction-context"
import { useRunContext } from "@/context/run-context"

export function BnBTree() {
  return (
    <ReactFlowProvider>
      <DirectionProvider initial="TB">
        <BnBTreeCanvas />
      </DirectionProvider>
    </ReactFlowProvider>
  )
}

function BnBTreeCanvas() {
  const { theme } = useTheme()
  const { runData } = useRunContext()

  const { nodes: initialNodes, edges: initialEdges } = toReactFlow(runData)
  // layouts are pure functions of the static mock — precompute both once,
  // toggling direction is then a zero-cost array swap
  const layouts = useMemo(
    () =>
      ({
        TB: layoutTree(initialNodes, initialEdges, "TB", 30, 42),
        LR: layoutTree(initialNodes, initialEdges, "LR", 8, 96),
      }) as const,
    [initialNodes, initialEdges]
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(layouts.TB)
  const { direction, setDirection } = useDirectionContext()
  const { fitView } = useReactFlow<BnBFlowNode>()

  const handleToggleLayout = useCallback(() => {
    const next: Direction = direction === "TB" ? "LR" : "TB"
    setDirection(next)
    setNodes(layouts[next])
    requestAnimationFrame(() => fitView({ duration: 0 }))
  }, [direction, setDirection, setNodes, fitView, layouts])

  return (
    <ReactFlow
      nodes={nodes}
      edges={initialEdges}
      onNodesChange={onNodesChange}
      nodeTypes={nodeTypes}
      colorMode={theme}
      nodesDraggable={false}
      minZoom={0.1}
      fitView
    >
      <MiniMap
        nodeComponent={MiniMapNode}
        pannable
        zoomable
        position="bottom-left"
      />
      <Controls
        showInteractive={false}
        position="bottom-right"
        className="shadow-lg"
      >
        <ControlButton onClick={handleToggleLayout} title="Change Layout">
          {direction === "TB" ? <ArrowLeftRight /> : <ArrowDownUp />}
        </ControlButton>
      </Controls>
      <Panel position="top-left">
        <Legend />
      </Panel>
      <Panel position="top-right" className="flex gap-1">
        {/* label/icon shows the direction you will switch TO */}
        <Button
          variant="outline"
          onClick={handleToggleLayout}
          title="Change Layout"
          className="shadow-sm active:not-aria-[haspopup]:shadow-none"
        >
          {direction === "TB" ? <ArrowLeftRight /> : <ArrowDownUp />}
          Change layout
        </Button>
        <Button
          variant="outline"
          onClick={() => fitView()}
          title="Fit View"
          className="shadow-sm active:not-aria-[haspopup]:shadow-none"
        >
          <Maximize /> Fit view
        </Button>
      </Panel>
      <Panel position="bottom-center">
        <TimeLine />
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
