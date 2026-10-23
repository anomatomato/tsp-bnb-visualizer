import type { SolverConfigData } from "@/types/api-types"

export type SolverConfigRow = {
  label: string
  description: string
  id: string
}

export function solverConfigRows(c: SolverConfigData): SolverConfigRow[] {
  return [
    {
      label: c.search_policy_label,
      description: c.search_policy_description,
      id: c.search_policy,
    },
    {
      label: c.branching_strategy_label,
      description: c.branching_strategy_description,
      id: c.branching_strategy,
    },
    {
      label: c.relaxation_label,
      description: c.relaxation_description,
      id: c.relaxation,
    },
    {
      label: c.root_heuristics_label,
      description: c.root_heuristics_description,
      id: c.root_heuristics,
    },
  ]
}

export function solverConfigSummary(c: SolverConfigData): string {
  return solverConfigRows(c)
    .map((r) => r.label)
    .join(" · ")
}
const thisYear = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  hour: "2-digit",
  hourCycle: "h23",
  minute: "2-digit",
})

const withYear = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  hourCycle: "h23",
  minute: "2-digit",
})

export function formatRunDate(date: string | null | undefined): string {
  if (date === null || date === undefined) return "-"

  const d = new Date(date)
  if (Number.isNaN(d.getTime())) return "-" // corrupt entry, don't throw in render

  const fmt = d.getFullYear() === new Date().getFullYear() ? thisYear : withYear
  return fmt.format(d)
}
