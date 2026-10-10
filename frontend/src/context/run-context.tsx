import {
  createContext,
  use,
  useEffect,
  useState,
  useTransition,
  type ReactNode,
} from "react"
import type { BnBRunData } from "@/types/api-types"
import {
  fetchRunIndex,
  getRunId,
  initialRunIndexPromise,
  fetchRunData,
  type RunIndexEntry,
} from "@/lib/run"
import { Button } from "@/components/ui/button"
import { Centered } from "@/components/layouts/centered"

interface RunContextValue {
  runId: string
  runData: BnBRunData // consumed via use() under Suspense
  runIndex: RunIndexEntry[] // catalog for the run picker
  isPending: boolean // data is still fetching
  selectRun: (runId: string) => void
  refreshIndex: () => void
}

const RunContext = createContext<RunContextValue | undefined>(undefined)

export function RunProvider({ children }: { children: ReactNode }) {
  const initialIndex = use(initialRunIndexPromise) // suspends until catalog loads
  const [runIndex, setRunIndex] = useState<RunIndexEntry[]>(initialIndex)
  const [runId, setRunId] = useState<string | null>(() =>
    getRunId(initialIndex)
  )
  const [isPending, startTransition] = useTransition()

  // change run id when use navigates the session hisotry
  useEffect(() => {
    const handlePopState = () => {
      const id = getRunId(runIndex)
      startTransition(() => {
        setRunId(id)
      })
    }
    window.addEventListener("popstate", handlePopState)
    return () => window.removeEventListener("popstate", handlePopState)
  }, [runIndex])

  // URL mirror: the address bar must always agree with runId. Covers every fallback path (bookmarked-then-deleted run), where getRunId picked something other than what the URL claims.
  useEffect(() => {
    if (runId === null) return //NoRunsNotice: nothing to mirror

    const url = new URL(location.href)
    if (url.searchParams.get("run") !== runId) {
      url.searchParams.set("run", runId)
      history.replaceState(null, "", url)
    }
  }, [runId])

  const refreshIndex = () => {
    void fetchRunIndex() // void: fire-and-forget; errors land in .catch
      .then((index) => {
        startTransition(() => {
          setRunIndex(index)
          // Keep the current run if it still exists; otherwise re-derive.
          // Covers the empty-catalog on mount AND a deleted current run
          setRunId((current) =>
            current !== null && index.some((entry) => entry.id === current)
              ? current
              : getRunId(index)
          )
        })
      })
      .catch((error) => console.error("run catalog refresh failed:", error))
  }

  // Empty catalog is a UI state
  if (runId === null) {
    return <NoRunsNotice onRefresh={refreshIndex} />
  }

  const runData = use(fetchRunData(runId))

  const selectRun = (id: string) => {
    if (id === runId) return // don't stack duplicate history entries

    const url = new URL(location.href)
    url.searchParams.set("run", id) // preserves other params + hash
    history.pushState(null, "", url)
    startTransition(() => setRunId(id)) // old run stays visible until new data arrives
  }

  const value: RunContextValue = {
    runId,
    runData,
    runIndex,
    isPending,
    selectRun,
    refreshIndex,
  }

  return <RunContext value={value}>{children}</RunContext>
}

function NoRunsNotice({ onRefresh }: { onRefresh: () => void }) {
  return (
    <Centered className="gap-6">
      <h2 className="text-2xl font-semibold">No runs available</h2>
      <p className="text-muted-foreground">
        Run <code>uv run python -m examples.run_tsplib</code> to export a run,
        then refresh.
      </p>
      <Button onClick={onRefresh}>Refresh</Button>
    </Centered>
  )
}

export function useRunContext() {
  const context = use(RunContext)
  if (!context) {
    throw new Error("useRunContext must be used within a RunProvider")
  }
  return context
}
