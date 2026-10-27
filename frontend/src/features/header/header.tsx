import { ModeToggle } from "@/components/mode-toggle"
import { useRunContext } from "@/context/run-context"
import { RunPicker } from "./components/run-picker"
import { SolverConfig } from "./components/solver-config"

export function Header() {
  const { runData } = useRunContext()
  return (
    <header className="flex h-16 shrink-0 items-center gap-4 border-b px-6">
      <h1 className="font-bold">
        TSP Branch & Bound Visualization ({runData.instance.name})
      </h1>
      <p className="text-sm text-muted-foreground">
        {runData.instance.nodes.length} nodes ·{" "}
        {runData.processing_order.length} iterations · optimal cost{" "}
        {runData.best_solutions.at(-1)?.cost.toFixed(2)}
        <SolverConfig />
      </p>
      <div className="ml-auto flex gap-4">
        <RunPicker />
        <ModeToggle />
      </div>
    </header>
  )
}
