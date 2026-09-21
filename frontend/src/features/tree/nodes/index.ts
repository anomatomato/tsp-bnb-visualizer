import type { NodeTypes } from "@xyflow/react"
import { BnBTreeNode } from "./bnb-tree-node"

export const nodeTypes = {
  bnb: BnBTreeNode,
} as const satisfies NodeTypes
