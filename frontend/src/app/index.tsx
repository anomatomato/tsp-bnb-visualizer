import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { BnBTree } from "@/features/tree/tree"
import Inspector from "@/features/inspector/inspector"
import { useRunContext } from "@/context/run-context"
import AppProvider from "./provider"
import { Header } from "./header"

export function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  )
}

function AppShell() {
  const { runData } = useRunContext()

  return (
    <>
      <title>{`TSP BnB (${runData.instance.name})`}</title>
      <div className="flex h-svh flex-col">
        <Header />
        <main className="flex-1">
          <ResizablePanelGroup orientation="horizontal">
            <ResizablePanel minSize="192px" defaultSize="75">
              <BnBTree />
            </ResizablePanel>
            <ResizableHandle />
            <ResizablePanel minSize="192px">
              <Inspector />
            </ResizablePanel>
          </ResizablePanelGroup>
        </main>
      </div>
    </>
  )
}

export default App
