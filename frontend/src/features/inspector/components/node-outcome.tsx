import { useRunContext } from "@/context/run-context"
import { explainOutcome, type FlatNode } from "@/lib/bnb"
import { Section } from "./section"

export function NodeOutcome({ node }: { node: FlatNode }) {
  const { runData } = useRunContext()

  return (
    <Section title="Outcome" defaultOpen>
      <p className="leading-normal">
        {explainOutcome(node, runData.instance.edges)}
      </p>
      <dl className="flex flex-col gap-1">
        <div className="flex justify-between gap-6">
          <dt className="text-muted-foreground">LP Bound (LB)</dt>
          <dd className="tabular-nums">
            {node.relaxed_solution?.objective.toFixed(2) ?? "–"}
          </dd>
        </div>
        <div className="flex justify-between gap-6">
          <dt className="text-muted-foreground">Global (LB)</dt>
          <dd className="tabular-nums">{node.lb?.toFixed(2) ?? "–"}</dd>
        </div>
        <div className="flex justify-between gap-6">
          <dt className="text-muted-foreground">Incumbent (UB)</dt>
          <dd className="tabular-nums">{node.ub?.toFixed(2) ?? "–"}</dd>
        </div>
      </dl>
    </Section>
  )
}
