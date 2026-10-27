import { useRunContext } from "@/context/run-context"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { CheckIcon, ChevronsUpDown } from "lucide-react"
import { formatRunDate } from "@/lib/format"
import { cn } from "cn"
import type { RunIndexEntry } from "@/lib/run"

export function RunPicker() {
  const { runIndex, runId, selectRun, runData } = useRunContext()
  const recent = runIndex.slice(0, 5)
  const groups = Object.groupBy(runIndex, (entry) => entry.name)

  const renderItem = (entry: RunIndexEntry, showName: boolean = true) => (
    <DropdownMenuItem
      key={entry.id}
      onClick={() => {
        selectRun(entry.id)
      }}
      className="justify-between"
    >
      {showName && <span className="truncate font-medium">{entry.name}</span>}
      <span className="flex items-center gap-1 text-muted-foreground">
        <time dateTime={entry.date ?? undefined} className="tabular-nums">
          {formatRunDate(entry.date)}
        </time>
        <CheckIcon
          aria-hidden="true"
          className={cn("size-4", runId !== entry.id && "invisible")}
        />
      </span>
    </DropdownMenuItem>
  )

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="outline"
            className="max-w-md min-w-32 justify-between gap-4 shadow-sm"
          />
        }
      >
        <span className="truncate font-medium">{runData.instance.name}</span>
        <span className="flex items-center gap-1 text-muted-foreground">
          <time
            dateTime={runData.started_at ?? undefined}
            className="tabular-nums"
          >
            {formatRunDate(runData.started_at)}
          </time>
          <ChevronsUpDown aria-hidden="true" className="size-4" />
        </span>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-96">
        <DropdownMenuGroup>
          <DropdownMenuLabel>Recent Runs</DropdownMenuLabel>
          {recent.map((entry) => renderItem(entry, true))}
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        {Object.entries(groups).map(([name, entries]) => (
          <DropdownMenuSub key={name}>
            <DropdownMenuSubTrigger className="[&>svg]:ml-0">
              <span className="truncate font-medium">{name}</span>
              <span className="ml-auto text-muted-foreground tabular-nums">
                {entries?.length}
              </span>
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              {entries?.map((entry) => renderItem(entry, false))}
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
