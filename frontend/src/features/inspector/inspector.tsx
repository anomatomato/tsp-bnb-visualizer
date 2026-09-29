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
import { type FlatNode, incumbentAt } from "@/lib/bnb"
import { resolveImage } from "@/lib/images"
import type {
  BestSolutionEntry,
  BnBRunData,
  NodeStatus,
} from "@/types/api-types"
import { statusBadgeClasses } from "@/lib/status"
import { ScrollArea } from "@/components/ui/scroll-area"

interface InspectorProps {
  node?: FlatNode
  incumbent: BestSolutionEntry | null
}

const svg = (path: string | null | undefined) => {
  if (!path) return null
  return <img src={resolveImage(path) ?? ""} />
}

export default function Inspector({ node, incumbent }: InspectorProps) {
  if (!node) {
    return <div>No existing node data</div>
  }
  return (
    <ScrollArea>
      <div className="flex flex-col gap-4 p-4 text-sm">
        <header className="flex items-center gap-3">
          <Badge className={`${statusBadgeClasses[node.status]}`}>
            {node.status}
          </Badge>
          <span>
            #{node.node_id} · depth {node.depth}
          </span>
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
            {svg(node.relaxed_solution?.image_path) ?? "No relaxed solution"}
          </TabsContent>
          <TabsContent value="incumbent">
            {svg(incumbent?.image_path) ?? "No incumbent solution"}
          </TabsContent>
          <TabsContent value="heuristic">
            {svg(node.heuristic_solution?.image_path) ??
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
