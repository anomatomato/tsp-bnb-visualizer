import { Badge } from "@/components/ui/badge"
import { statusBadgeClass } from "@/lib/status"
import type { FlatNode } from "@/lib/bnb"
import DistanceMatrix from "./distance-matrix"

export default function NodeHeader({ node }: { node: FlatNode }) {
  return (
    <header className="flex items-center gap-3">
      <Badge className={statusBadgeClass(node.status)}>
        {node.status ?? "Open"}
      </Badge>
      <span title={`depth = ${node.depth + 1}`}>↓ {node.depth + 1}</span>
      <div className="ml-auto">
        <DistanceMatrix />
      </div>
    </header>
  )
}
