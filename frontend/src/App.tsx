import { ModeToggle } from "@/components/mode-toggle"
import { Button } from "@/components/ui/button"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { BnBTree } from "@/features/tree/tree"
import run from "@/mock/eil51/bnb_state.json"

export function App() {
  return (
    <div className="flex min-h-svh flex-col gap-6 p-4">
      <header className="flex h-16 shrink-0 items-center gap-6 border-b px-6">
        <h1 className="font-bold">{run.instance.name}</h1>
        <p className="text-sm text-muted-foreground">
          {run.instance.nodes.length} nodes · {run.processing_order.length}{" "}
          iterations · optimum {run.best_solutions.at(-1)?.cost.toFixed(1)}
        </p>
      </header>

      <main>
        <ResizablePanelGroup orientation="horizontal">
          <ResizablePanel minSize="50" defaultSize="75">
            <BnBTree />
          </ResizablePanel>
          <ResizableHandle />
          <ResizablePanel>
            <div className="flex max-w-md min-w-0 flex-col gap-4 text-sm leading-loose">
              <div>
                <h1 className="font-medium">Project ready!</h1>
                <p>You may now add components and start building.</p>
                <p>We&apos;ve already added the button component for you.</p>
                <ModeToggle />
                <Button className="mt-2">Button</Button>
              </div>
              <div className="font-mono text-xs text-muted-foreground">
                (Press <kbd>d</kbd> to toggle dark mode)
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </main>

      <footer>footer</footer>
    </div>
  )
}

export default App
