import { ScrollArea } from "@/components/ui/scroll-area"
import { toNodeMap } from "@/lib/bnb"
import { useRunContext } from "@/context/run-context"
import { useIterationContext } from "@/context/iteration-context"
import { NodeHeader } from "./components/node-header"
import { BranchDecisions } from "./components/branch-decisions"
import { FractionalEdges } from "./components/fractional-edges"
import { NodeOutcome } from "./components/node-outcome"
import { Solutions } from "./components/solutions"

export default function Inspector() {
  const { runData } = useRunContext()
  const { iteration } = useIterationContext()

  const nodeMap = toNodeMap(runData)
  const currentNodeId = runData.processing_order[iteration - 1]
  const node = nodeMap.get(currentNodeId)

  if (!node) {
    return <div>No existing node data</div>
  }

  const parent =
    node.parent_id !== null ? nodeMap.get(node.parent_id) : undefined

  return (
    <ScrollArea className="h-full">
      <div className="@container flex flex-col gap-4 p-4 text-sm">
        <NodeHeader node={node} />
        <NodeOutcome node={node} />
        <Solutions node={node} />
        <BranchDecisions node={node} parent={parent} />
        <FractionalEdges node={node} />
      </div>
    </ScrollArea>
  )
}
