import { useRunContext } from "@/context/run-context"
import type { FlatNode } from "@/lib/bnb"
import { TourSvg } from "./tour-svg"
import { Section } from "./section"

export default function ProducedSolutions({ node }: { node: FlatNode }) {
  const { runData } = useRunContext()
  const instance = runData.instance
  const heuristic = node.heuristic_solution
  const lp = node.relaxed_solution
  const incumbent = node.status === "Integer" && lp !== null

  return (
    <Section title="Solutions produced" defaultOpen>
      {!heuristic && !incumbent && (
        <p className="text-muted-foreground">This node produced no tour.</p>
      )}
      {heuristic && (
        <div className="flex flex-col gap-1">
          <p className="text-muted-foreground">
            Heuristic tour, cost{" "}
            <span className="tabular-nums">{heuristic.cost.toFixed(2)}</span>
          </p>
          <TourSvg
            positions={instance.nodes}
            edges={instance.edges}
            values={heuristic.edge_selection}
            mode="tour"
          />
        </div>
      )}
      {incumbent && lp && (
        <div className="flex flex-col gap-1">
          <p className="text-muted-foreground">
            Integral tour — became the incumbent, cost{" "}
            <span className="tabular-nums">{lp.objective.toFixed(2)}</span>
          </p>
          <TourSvg
            positions={instance.nodes}
            edges={instance.edges}
            values={lp.edge_fractions}
            mode="tour"
          />
        </div>
      )}
    </Section>
  )
}
