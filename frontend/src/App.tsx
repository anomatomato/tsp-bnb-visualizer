import { ModeToggle } from "@/components/mode-toggle"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { TimeLine } from "@/features/timeline/timeline"
import { BnBTree } from "@/features/tree/tree"
import run from "@/mock/eil51/bnb_state.json"
import { useState } from "react"
import Inspector from "@/features/inspector/inspector"
import { incumbentAt, toNodeMap } from "@/lib/bnb"
import type { BnBRunData } from "@/types/api-types"

const bnbRun = run as BnBRunData
const nodeMap = toNodeMap(bnbRun)

export function App() {
  const [iteration, setIteration] = useState<number>(
    run.processing_order.length
  )
  const currentNodeId = run.processing_order[iteration - 1]
  const currentNode = nodeMap.get(currentNodeId)
  const currentIncumbent = incumbentAt(bnbRun, iteration)

  return (
    <div className="flex h-svh flex-col">
      <header className="flex h-16 shrink-0 items-center gap-6 border-b px-6">
        <h1 className="font-bold">
          TSP Branch & Bound Visualization{" "}
          <span className="italic">({run.instance.name})</span>
        </h1>
        <p className="text-sm text-muted-foreground">
          {run.instance.nodes.length} nodes · {run.processing_order.length}{" "}
          iterations · optimal cost {run.best_solutions.at(-1)?.cost.toFixed(1)}
        </p>
        <div className="ml-auto">
          <ModeToggle />
        </div>
      </header>

      <main className="flex-1">
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel minSize="192px" defaultSize="75">
            <BnBTree iteration={iteration} />
          </ResizablePanel>
          <ResizableHandle />
          <ResizablePanel minSize="192px">
            <Inspector node={currentNode} incumbent={currentIncumbent} />
          </ResizablePanel>
        </ResizablePanelGroup>
      </main>

      <footer>
        <TimeLine
          iteration={iteration}
          max={run.processing_order.length}
          setIteration={setIteration}
        />
      </footer>
    </div>
  )
}

export default App
