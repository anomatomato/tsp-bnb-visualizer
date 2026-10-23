import { useIterationContext } from "@/context/iteration-context"
import { useRunContext } from "@/context/run-context"
import { incumbentAt, type FlatNode } from "@/lib/bnb"
import { Section } from "./section"
import { TourSvg } from "./tour-svg"

/**
 * The three solution drawings, stacked full-width so the shared TourSvg
 * normalization makes them pixel-aligned and vertically diffable.
 *
 * Relaxed and Incumbent always render — absence is story ("no incumbent
 * yet", "LP infeasible"). Heuristic only exists at the root, so it renders
 * conditionally.
 */
export function Solutions({ node }: { node: FlatNode }) {
  const { runData } = useRunContext()
  const { iteration } = useIterationContext()
  const instance = runData.instance

  const lp = node.relaxed_solution
  const heuristic = node.heuristic_solution
  const incumbent = incumbentAt(runData, iteration)

  // The warm-start incumbent (iteration 0) is produced by the root's
  // heuristic; every later entry by the node processed at its iteration.
  const warmStart = incumbent?.iteration === 0
  const producedHere =
    incumbent !== null &&
    (warmStart
      ? node.node_id === runData.tree.node_id
      : runData.processing_order[incumbent.iteration - 1] === node.node_id)

  return (
    <>
      <div className="grid grid-cols-1 gap-1 @min-lg:grid-cols-2">
        <Section title="Relaxed (LP)" defaultOpen>
          {lp ? (
            <div className="flex flex-col gap-1">
              <p className="text-muted-foreground">
                LP bound{" "}
                <span className="tabular-nums">{lp.objective.toFixed(2)}</span>
              </p>
              <TourSvg
                positions={instance.nodes}
                edges={instance.edges}
                values={lp.edge_fractions}
                mode="lp"
              />
            </div>
          ) : (
            <p className="text-muted-foreground">
              No LP solution — infeasible under this node&apos;s fixations.
            </p>
          )}
        </Section>
        <Section title="Incumbent" defaultOpen>
          {incumbent ? (
            <div className="flex flex-col gap-1">
              <p className="text-muted-foreground">
                Best tour so far, cost{" "}
                <span className="tabular-nums">
                  {incumbent.cost.toFixed(2)}
                </span>
                {producedHere &&
                  (warmStart
                    ? " — this node's warm start"
                    : " — produced by this node")}
              </p>
              <TourSvg
                positions={instance.nodes}
                edges={instance.edges}
                values={incumbent.edge_selection}
                mode="tour"
              />
            </div>
          ) : (
            <p className="text-muted-foreground">
              No incumbent yet at iteration {iteration}.
            </p>
          )}
        </Section>
      </div>
      {heuristic && (
        <Section title="Heuristic" defaultOpen>
          <div className="flex flex-col gap-1">
            <p className="text-muted-foreground">
              Warm-start tour, cost{" "}
              <span className="tabular-nums">{heuristic.cost.toFixed(2)}</span>
            </p>
            <TourSvg
              positions={instance.nodes}
              edges={instance.edges}
              values={heuristic.edge_selection}
              mode="tour"
            />
          </div>
        </Section>
      )}
    </>
  )
}
