import { Badge } from "@/components/ui/badge"
import { statusBadgeClass } from "@/lib/status"
import type { FlatNode } from "@/lib/bnb"
import { DistanceMatrix } from "./distance-matrix"
import { useIterationContext } from "@/context/iteration-context"

export function NodeHeader({ node }: { node: FlatNode }) {
  const { iteration } = useIterationContext()
  return (
    <header className="flex items-center gap-2">
      <Badge className={statusBadgeClass(node.status)}>
        {node.status ?? "Open"}
      </Badge>
      <span className="text-muted-foreground">
        #{iteration} · depth {node.depth + 1}
      </span>
      <div className="ml-auto">
        <DistanceMatrix />
      </div>
    </header>
  )
}
