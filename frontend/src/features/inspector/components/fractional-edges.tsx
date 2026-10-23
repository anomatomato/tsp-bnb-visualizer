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

export function FractionalEdges({ node }: { node: FlatNode }) {
  const { runData } = useRunContext()
  const lp = node.relaxed_solution
  const fractional = lp ? fractionalEdges(node) : []

  return (
    <Section title="Fractional edges">
      {!lp ? (
        <p className="text-muted-foreground">
          No LP snapshot — this node was never processed.
        </p>
      ) : fractional.length === 0 ? (
        <p className="text-muted-foreground">
          No fractional edges — the LP solution is integral.
        </p>
      ) : (
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
                <TableCell>{edgeLabel(runData.instance.edges, i)}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {lp.edge_fractions[i]?.toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Section>
  )
}
