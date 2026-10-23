import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useRunContext } from "@/context/run-context"
import { solverConfigRows, solverConfigSummary } from "@/lib/format"

/**
 * The " — best-bound · most-fractional branching · …" span in the header
 * subtitle, with a rich tooltip exposing each component's label,
 * description, and machine identifier.
 */
export function SolverConfig() {
  const { runData } = useRunContext()
  const config = runData.solver_config

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span className="cursor-help">
            {" — "}
            {solverConfigSummary(config)}
          </span>
        }
      />
      <TooltipContent
        side="bottom"
        align="start"
        className="flex max-w-64 flex-col items-start gap-2 text-left"
      >
        {solverConfigRows(config).map((row) => (
          <div key={row.label} className="flex flex-col">
            <p>
              <span className="font-semibold">{row.label}</span>
              {row.description ? ` — ${row.description}` : ""}
            </p>
            <p className="opacity-60">{row.id}</p>
          </div>
        ))}
      </TooltipContent>
    </Tooltip>
  )
}
