import { useRunContext } from "@/context/run-context"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  // DropdownMenuItem,
  DropdownMenuLabel,
  // DropdownMenuPortal,
  // DropdownMenuSeparator,
  // DropdownMenuShortcut,
  // DropdownMenuSub,
  // DropdownMenuSubContent,
  // DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { ChevronsUpDown } from "lucide-react"

export default function RunPicker() {
  const { runIndex, runId, selectRun, runData } = useRunContext()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="secondary" />}>
        <span className="font-bold">{runData.instance.name}</span>
        <span>
          {runData.started_at} <ChevronsUpDown />
        </span>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-96">
        <DropdownMenuGroup>
          <DropdownMenuLabel>Recent Runs</DropdownMenuLabel>
          {runIndex.slice(0, 5).map((entry) => {
            return (
              <DropdownMenuCheckboxItem
                key={entry.id}
                checked={runId === entry.id}
                onClick={() => {
                  selectRun(entry.id)
                }}
              >
                <strong>{entry.name}</strong> · {entry.date}
              </DropdownMenuCheckboxItem>
            )
          })}
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
