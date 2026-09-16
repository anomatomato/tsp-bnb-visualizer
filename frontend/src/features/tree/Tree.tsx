import {
  Background,
  ControlButton,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type MiniMapNodeProps,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { initialEdges, initialNodes, nodeTypes } from "./nodes"

export function BnBTree() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  return (
    <div style={{ height: "100%", width: "100%" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        colorMode="system"
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
  return (
    <circle
      cx={x}
      cy={y}
      r="30"
      fill="#7c2ff7"
      className="fill-pink-500"
      opacity={0.5}
    />
  )
}
