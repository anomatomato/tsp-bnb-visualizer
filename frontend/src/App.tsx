import { ModeToggle } from "@/components/mode-toggle"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { BnBTree } from "@/features/tree/tree"
import runJson from "@/mock/eil51/bnb_state.json"
import Inspector from "@/features/inspector/inspector"
import { incumbentAt, toNodeMap } from "@/lib/bnb"
import type { BnBRunData } from "@/types/api-types"
import {
  IterationProvider,
  useIterationContext,
} from "@/context/iteration-context"

const run = runJson as BnBRunData
const nodeMap = toNodeMap(run)

export function App() {
  return (
    <IterationProvider max={run.processing_order.length}>
      <AppShell />
    </IterationProvider>
  )
}

function AppShell() {
  const { iteration } = useIterationContext()
  const currentNodeId = run.processing_order[iteration - 1]
  const currentNode = nodeMap.get(currentNodeId)
  const currentIncumbent = incumbentAt(run, iteration)

  return (
    <>
      <title>TSP BnB</title>
      <div className="flex h-svh flex-col">
        <header className="flex h-16 shrink-0 items-center gap-6 border-b px-6">
          <h1 className="font-bold">
            TSP Branch & Bound Visualization{" "}
            <span className="italic">({run.instance.name})</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            {run.instance.nodes.length} nodes · {run.processing_order.length}{" "}
            iterations · optimal cost{" "}
            {run.best_solutions.at(-1)?.cost.toFixed(2)}
          </p>
          <div className="ml-auto">
            <ModeToggle />
          </div>
        </header>

        <main className="flex-1">
          <ResizablePanelGroup orientation="horizontal">
            <ResizablePanel minSize="192px" defaultSize="75">
              <BnBTree />
            </ResizablePanel>
            <ResizableHandle />
            <ResizablePanel minSize="192px">
              <Inspector node={currentNode} incumbent={currentIncumbent} />
            </ResizablePanel>
          </ResizablePanelGroup>
        </main>
      </div>
    </>
  )
}

export default App
