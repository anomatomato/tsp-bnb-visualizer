import { useRunContext } from "@/context/run-context"
import { edgeLabel, fixedEdgesOf, ownBranch, type FlatNode } from "@/lib/bnb"
import { Section } from "./section"

export default function BranchDecisions({
  node,
  parent,
}: {
  node: FlatNode
  parent?: FlatNode
}) {
  const { runData } = useRunContext()
  const edges = runData.instance.edges
  const { fixedIn, fixedOut } = fixedEdgesOf(node)
  const branch = parent ? ownBranch(node, parent) : null
  const none = fixedIn.length + fixedOut.length === 0

  return (
    <Section title="Branch decisions">
      {none ? (
        <p className="text-muted-foreground">No fixed edges.</p>
      ) : (
        <>
          <p className="text-muted-foreground">
            Fixed in ({fixedIn.length}):{" "}
            {fixedIn.map((i) => edgeLabel(edges, i)).join(", ") || "–"}
          </p>
          <p className="text-muted-foreground">
            Fixed out ({fixedOut.length}):{" "}
            {fixedOut.map((i) => edgeLabel(edges, i)).join(", ") || "–"}
          </p>
        </>
      )}
      {branch && (
        <p className="text-muted-foreground">
          Created by branching on edge {edgeLabel(edges, branch.edge)}: this
          child {branch.side === 1 ? "includes" : "excludes"} it.
        </p>
      )}
    </Section>
  )
}
