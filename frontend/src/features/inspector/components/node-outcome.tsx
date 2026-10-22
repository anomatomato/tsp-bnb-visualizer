import { useRunContext } from "@/context/run-context"
import { explainOutcome, type FlatNode } from "@/lib/bnb"
import { Section } from "./section"

export default function NodeOutcome({ node }: { node: FlatNode }) {
  const { runData } = useRunContext()

  return (
    <Section title="Outcome" defaultOpen>
      <p className="leading-normal">
        {explainOutcome(node, runData.instance.edges)}
      </p>
      <dl className="flex flex-col gap-1">
        <div className="flex justify-between gap-6">
          <dt className="text-muted-foreground">Created at iteration</dt>
          <dd className="tabular-nums">{node.created_at}</dd>
        </div>
        <div className="flex justify-between gap-6">
          <dt className="text-muted-foreground">Processed at iteration</dt>
          <dd className="tabular-nums">{node.processed_at ?? "–"}</dd>
        </div>
        <div className="flex justify-between gap-6">
          <dt className="text-muted-foreground">Pruned at iteration</dt>
          <dd className="tabular-nums">{node.pruned_at ?? "–"}</dd>
        </div>
      </dl>
    </Section>
  )
}
