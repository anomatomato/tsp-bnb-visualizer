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
