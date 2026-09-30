import type { NodeStatus } from "@/types/api-types"

/** tree node fill: status tint + stroke */
export const statusNodeClasses: Record<NodeStatus, string> = {
  Branched: "bg-bnb-status-branched/50 border-bnb-status-branched",
  Feasible: "bg-bnb-status-feasible/50 border-bnb-status-feasible",
  Infeasible: "bg-bnb-status-infeasible/50 border-bnb-status-infeasible",
  Pruned: "bg-bnb-status-pruned/50 border-bnb-status-pruned",
}

export const neutralNodeClasses = "bg-muted/50 border-muted-foreground"
export const statusNodeClass = (s: NodeStatus | null) =>
  s === null ? neutralNodeClasses : statusNodeClasses[s]

export const statusBadgeClasses: Record<NodeStatus, string> = {
  Feasible: "bg-bnb-status-feasible",
  Branched: "bg-bnb-status-branched",
  Pruned: "bg-bnb-status-pruned",
  Infeasible: "bg-bnb-status-infeasible",
}

export const neutralBadgeClass = "bg-muted"
export const statusBadgeClass = (s: NodeStatus | null) =>
  s === null ? neutralBadgeClass : statusBadgeClasses[s]
