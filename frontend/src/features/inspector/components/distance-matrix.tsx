import { useState } from "react"
import { Check, Copy } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useRunContext } from "@/context/run-context"

/** Cell text for the copy payload — "" on the diagonal / missing edges. */
const cellText = (
  u: number,
  v: number,
  weight: (u: number, v: number) => number | undefined
) => (u === v ? "" : (weight(u, v)?.toFixed(1) ?? ""))

export function DistanceMatrix() {
  const { runData } = useRunContext()
  const nodes = runData.instance.nodes
  const [copied, setCopied] = useState(false)

  // "u-v" with u < v → weight; O(1) lookup, no per-cell edge scan
  const weights = new Map(
    runData.instance.edges.map((e) => [
      `${Math.min(e.u, e.v)}-${Math.max(e.u, e.v)}`,
      e.weight,
    ])
  )
  const weight = (u: number, v: number) =>
    weights.get(`${Math.min(u, v)}-${Math.max(u, v)}`)

  // TSV with row/column headers: pastes into any spreadsheet as a table
  // without an import wizard. The viewer serves from localhost (a secure
  // context), so navigator.clipboard is available.
  const asTsv = () => {
    const header = ["", ...nodes.map((n) => String(n.id))].join("\t")
    const rows = nodes.map((row) =>
      [
        String(row.id),
        ...nodes.map((col) => cellText(row.id, col.id, weight)),
      ].join("\t")
    )
    return [header, ...rows].join("\n")
  }

  const copy = async () => {
    await navigator.clipboard.writeText(asTsv())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Dialog>
      <DialogTrigger
        render={
          <Button variant="outline" size="sm">
            Matrix
          </Button>
        }
      />
      {/* w-fit: the dialog hugs the table's natural width instead of the
          default sm:max-w-sm (384px) — without this override the matrix
          spills out of the rounded box. max-w caps keep it inside the
          viewport; flex + min-h-0/flex-1 lets the wrapper own the scroll. */}
      <DialogContent className="flex max-h-[calc(100svh-96px)] w-fit max-w-[calc(100svw-48px)] flex-col sm:max-w-[calc(100svw-48px)]">
        <div className="flex items-start justify-between gap-4">
          <DialogHeader>
            <DialogTitle>Distance matrix — {runData.instance.name}</DialogTitle>
            <DialogDescription>
              {nodes.length} cities, symmetric weights
            </DialogDescription>
          </DialogHeader>
          <Button
            variant="outline"
            size="sm"
            className="shrink-0"
            onClick={() => void copy()}
          >
            {copied ? <Check /> : <Copy />}
            {copied ? "Copied" : "Copy TSV"}
          </Button>
        </div>
        <div className="min-h-0 flex-1 overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                {/* corner cell: pinned in BOTH axes; bg-popover matches the
                    dialog surface (bg-background leaves a visible seam) */}
                <TableHead className="sticky top-0 left-0 z-30 bg-popover" />
                {nodes.map((n) => (
                  <TableHead
                    key={n.id}
                    className="sticky top-0 z-20 bg-popover text-center tabular-nums"
                  >
                    {n.id}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {nodes.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="sticky left-0 z-20 bg-popover font-medium tabular-nums">
                    {row.id}
                  </TableCell>
                  {nodes.map((col) => {
                    // ?? null: a missing edge renders like the diagonal
                    // instead of crashing toFixed
                    const w =
                      row.id === col.id
                        ? null
                        : (weight(row.id, col.id) ?? null)
                    return (
                      <TableCell
                        key={col.id}
                        className="text-center text-muted-foreground tabular-nums"
                        title={
                          w === null ? undefined : `${row.id}–${col.id}: ${w}`
                        }
                      >
                        {w === null ? "–" : w.toFixed(1)}
                      </TableCell>
                    )
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </DialogContent>
    </Dialog>
  )
}
