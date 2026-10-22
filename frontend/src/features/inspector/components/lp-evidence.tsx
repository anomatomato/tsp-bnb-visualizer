import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useRunContext } from "@/context/run-context"
import { edgeLabel, fractionalEdges, type FlatNode } from "@/lib/bnb"
import { Section } from "./section"

export default function LpEvidence({ node }: { node: FlatNode }) {
  const { runData } = useRunContext()
  const instance = runData.instance
  const lp = node.relaxed_solution
  const fractional = lp ? fractionalEdges(node) : []

  return (
    <Section title="LP relaxation" defaultOpen>
      {!lp ? (
        <p className="text-muted-foreground">
          No LP snapshot — this node was never processed.
        </p>
      ) : (
        <>
          <dl className="flex flex-col gap-1">
            <div className="flex justify-between gap-6">
              <dt className="text-muted-foreground">
                Objective (node lower bound)
              </dt>
              <dd className="tabular-nums">{lp.objective.toFixed(2)}</dd>
            </div>
            <div className="flex justify-between gap-6">
              <dt className="text-muted-foreground">GlobalLB at processing</dt>
              <dd className="tabular-nums">{node.lb?.toFixed(2) ?? "–"}</dd>
            </div>
            <div className="flex justify-between gap-6">
              <dt className="text-muted-foreground">Incumbent at decision</dt>
              <dd className="tabular-nums">{node.ub?.toFixed(2) ?? "–"}</dd>
            </div>
          </dl>
          {fractional.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fractional edge</TableHead>
                  <TableHead className="text-right">Fraction</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fractional.map((i) => (
                  <TableRow key={i}>
                    <TableCell>{edgeLabel(instance.edges, i)}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {lp.edge_fractions[i]?.toFixed(2)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </>
      )}
    </Section>
  )
}
