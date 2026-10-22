import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { incumbentAt, toNodeMap } from "@/lib/bnb"
import { resolveImage } from "@/lib/images"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useRunContext } from "@/context/run-context"
import { useIterationContext } from "@/context/iteration-context"
import NodeHeader from "./components/node-header"
import BranchDecisions from "./components/branch-decisions"
import LpEvidence from "./components/lp-evidence"
import NodeOutcome from "./components/node-outcome"
import ProducedSolutions from "./components/produced-solutions"

const svg = (path: string | null | undefined, runId: string) => {
  if (!path) return null
  return <img alt={path} src={resolveImage(path, runId) ?? ""} />
}

export default function Inspector() {
  const { runData, runId } = useRunContext()
  const { iteration } = useIterationContext()

  const nodeMap = toNodeMap(runData)
  const currentNodeId = runData.processing_order[iteration - 1]
  const node = nodeMap.get(currentNodeId)
  const incumbent = incumbentAt(runData, iteration)

  if (!node) {
    return <div>No existing node data</div>
  }

  const parent =
    node.parent_id !== null ? nodeMap.get(node.parent_id) : undefined

  return (
    <ScrollArea>
      <div className="flex flex-col gap-4 p-4 text-sm">
        <NodeHeader node={node} />
        {/* Act 1: decisions — fixedIn/fixedOut pair lists + own-branch diff
            (parent via nodeById/toNodeMap; thread map or parent prop in) */}
        {/* Act 2: LP — dl (objective), integral Badge, fractional-edge table, svg */}
        {/* Act 3: outcome — dl (created/processed), pruning-evidence sentence */}
        {/* Act 4: production — dl (cost), "improved incumbent" note, svg */}
        <Tabs defaultValue="relaxed">
          <TabsList>
            <TabsTrigger value="relaxed">Relaxed</TabsTrigger>
            <TabsTrigger value="incumbent">Incumbent</TabsTrigger>
            <TabsTrigger value="heuristic">Heuristic</TabsTrigger>
          </TabsList>
          <TabsContent value="relaxed">
            {svg(node.relaxed_solution?.image_path, runId) ??
              "No relaxed solution"}
          </TabsContent>
          <TabsContent value="incumbent">
            {svg(incumbent?.image_path, runId) ?? "No incumbent solution"}
          </TabsContent>
          <TabsContent value="heuristic">
            {svg(node.heuristic_solution?.image_path, runId) ??
              "No heuristic solution"}
          </TabsContent>
        </Tabs>
        <Table>
          <TableCaption>Total cost</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Relaxed</TableHead>
              <TableHead>Incumbent</TableHead>
              <TableHead>Heuristic</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>
                {node.relaxed_solution?.objective.toFixed(2) ?? "-"}
              </TableCell>
              <TableCell>{incumbent?.cost ?? "-"}</TableCell>
              <TableCell>{node.heuristic_solution?.cost ?? "-"}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
        <BranchDecisions node={node} parent={parent} />
        <LpEvidence node={node} />
        <NodeOutcome node={node} />
        <ProducedSolutions node={node} />
      </div>
    </ScrollArea>
  )
}
