import type { BnBRunData } from "@/types/api-types"

export type RunIndexEntry = {
  id: string
  name: string
  cost: number | null
  iterations: number
  /** When the run started — new runs: tz-aware ISO from BnBRunData.started_at; legacy runs: parsed from the run id. */
  date: string | null
}

export async function fetchRunIndex(): Promise<RunIndexEntry[]> {
  const result = await fetch("runs/index.json", { cache: "no-store" })
  if (!result.ok) throw new Error(`runs/index.json: ${result.status}`)
  return result.json()
}

export const initialRunIndexPromise: Promise<RunIndexEntry[]> = fetchRunIndex()

/**  promise-per-run cache: revisiting a run in-session is instant, no refetch machinery.
See more at https://react.dev/reference/react/use#caching-promises-for-client-components */
const runDataPromises = new Map<string, Promise<BnBRunData>>()

export function fetchRunData(runId: string): Promise<BnBRunData> {
  const cached = runDataPromises.get(runId)
  if (cached) return cached

  const fresh = fetch(`runs/${runId}/bnb_state.json`).then((response) => {
    if (!response.ok) {
      throw new Error(`bnb_state.json for ${runId}: ${response.status}`)
    }
    return response.json() as Promise<BnBRunData>
  })
  // Evict failures so the next mount retries. This side branch does NOT
  // rethrow - it resolves silently (no unhandled rejection), while `fresh`
  // itself still rejects for `use()` / the error boundary. The identity
  // guard ensures we only ever evict this promise's own entry.
  fresh.catch(() => {
    if (runDataPromises.get(runId) === fresh) runDataPromises.delete(runId)
  })
  runDataPromises.set(runId, fresh)
  return fresh
}

/** Resolve the active run id: the `?run=` param if it exists in the catalog, else the newest run.
 Pure - it also runs in a `useState` initializer, so
 no URL side effects in here (the URL-mirror effect owns those). */
export function getRunId(index: RunIndexEntry[]): string | null {
  if (index.length === 0) return null
  const requested = new URLSearchParams(location.search).get("run")
  return index.find((entry) => entry.id === requested)?.id ?? index[0].id
}
