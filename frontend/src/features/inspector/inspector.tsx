import { Badge } from "@/components/ui/badge"
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
import { statusBadgeClass } from "@/lib/status"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useRunContext } from "@/context/run-context"
import { useIterationContext } from "@/context/iteration-context"

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
  return (
    <ScrollArea>
      <div className="flex flex-col gap-4 p-4 text-sm">
        <header className="flex items-center gap-3">
          <Badge className={`${statusBadgeClass(node.status)}`}>
            {node.status ?? "never processed"}
          </Badge>
          <span title={`depth = ${node.depth + 1}`}>↓ {node.depth + 1}</span>
        </header>
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
      </div>
    </ScrollArea>
  )
}
