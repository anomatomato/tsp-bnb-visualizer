import { ModeToggle } from "@/components/mode-toggle"
import { Button } from "@/components/ui/button"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { TimeLine } from "@/features/timeline/timeline"
import { BnBTree } from "@/features/tree/tree"
import run from "@/mock/eil51/bnb_state.json"
import { useState } from "react"

export function App() {
  const [iteration, setIteration] = useState<number>(
    run.processing_order.length
  )
  const currentNodeId = run.processing_order[iteration - 1]

  return (
    <div className="flex h-svh flex-col">
      <header className="flex h-16 shrink-0 items-center gap-6 border-b px-6">
        <h1 className="font-bold">{run.instance.name}</h1>
        <p className="text-sm text-muted-foreground">
          {run.instance.nodes.length} nodes · {run.processing_order.length}{" "}
          iterations · optimum {run.best_solutions.at(-1)?.cost.toFixed(1)}
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
            <div className="flex max-w-md flex-col gap-4 text-sm leading-loose">
              <div>
                <h1 className="font-medium">Project ready!</h1>
                <p>You may now add components and start building.</p>
                <p>We&apos;ve already added the button component for you.</p>
                <Button className="mt-2">Button</Button>
              </div>
              <div className="font-mono text-xs text-muted-foreground">
                (Press <kbd>d</kbd> to toggle dark mode)
              </div>
            </div>
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
