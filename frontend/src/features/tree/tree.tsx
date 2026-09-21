import { useTheme } from "@/components/theme-provider"
import { toReactFlow } from "@/lib/bnb"
import { layoutTree } from "@/lib/layout"
import runJson from "@/mock/eil51/bnb_state.json"
import type { BnBRunData } from "@/types/api-types"
import {
  Background,
  ControlButton,
  Controls,
  MiniMap,
  ReactFlow,
  useNodesState,
  type MiniMapNodeProps,
} from "@xyflow/react"
import { nodeTypes } from "./nodes"

// tsc infers JSON string fields as `string`, not the generated literal
// unions — one typed cast at the boundary keeps toReactFlow type-safe.
const run = runJson as BnBRunData
const { nodes: rawNodes, edges } = toReactFlow(run)
const initialNodes = layoutTree(rawNodes, edges)

export function BnBTree() {
  const { theme } = useTheme()
  const [nodes, , onNodesChange] = useNodesState(initialNodes)

  return (
    <div className="size-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        nodeTypes={nodeTypes}
        colorMode={theme}
        fitView
      >
        <MiniMap nodeComponent={MiniMapNode} pannable zoomable />
        <Background />
        <Controls>
          <ControlButton
            onClick={() => alert("Something magical just happened. ✨")}
          >
            help
          </ControlButton>
        </Controls>
      </ReactFlow>
    </div>
  )
}

function MiniMapNode({ x, y }: MiniMapNodeProps) {
  return <circle cx={x} cy={y} r="30" className="fill-pink-500 opacity-50" />
}
