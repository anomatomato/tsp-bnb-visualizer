import { statusNodeClasses, statusDescription } from "@/lib/status"
import type { NodeStatus } from "@/types/api-types"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const statuses = Object.keys(statusNodeClasses) as NodeStatus[]

export default function Legend() {
  return (
    <div className="rounded-sm border px-3 py-2 text-sm shadow-md">
      <ul>
        {statuses.map((status) => (
          <Tooltip key={status}>
            <TooltipTrigger
              render={
                <li className="flex cursor-help items-center gap-2">
                  <span
                    className={`size-3 rounded-full ${statusNodeClasses[status]}`}
                  ></span>
                  <span>{status}</span>
                </li>
              }
            />
            <TooltipContent side="right">
              {statusDescription(status)}
            </TooltipContent>
          </Tooltip>
        ))}
      </ul>
      <p className="text-muted-foreground">label: LP bound</p>
    </div>
  )
}
