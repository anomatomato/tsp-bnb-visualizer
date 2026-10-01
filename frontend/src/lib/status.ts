import type { NodeStatus } from "@/types/api-types"

/** tree node fill: status tint + stroke */
export const statusNodeClasses: Record<NodeStatus, string> = {
  Branched: "bg-bnb-status-branched/50 border-bnb-status-branched",
  Integer: "bg-bnb-status-integer/50 border-bnb-status-integer",
  Infeasible: "bg-bnb-status-infeasible/50 border-bnb-status-infeasible",
  Pruned: "bg-bnb-status-pruned/50 border-bnb-status-pruned",
}

export const neutralNodeClasses = "bg-muted/50 border-muted-foreground"
export const statusNodeClass = (s: NodeStatus | null) =>
  s === null ? neutralNodeClasses : statusNodeClasses[s]

/** ring + glow color for the current-iteratio node */
export const statusCurrentNodeClasses: Record<NodeStatus, string> = {
  Branched: "ring-3 ring-bnb-status-branched shadow-bnb-status-branched",
  Integer: "ring-3 ring-bnb-status-integer shadow-bnb-status-integer",
  Infeasible: "ring-3 ring-bnb-status-infeasible shadow-bnb-status-infeasible",
  Pruned: "ring-3 ring-bnb-status-pruned shadow-bnb-status-pruned",
}
export const neutralCurrentNodeClasses =
  "ring-3 ring-muted-foreground shadow-muted-foreground"
export const statusCurrentNodeClass = (s: NodeStatus | null) =>
  s === null ? neutralCurrentNodeClasses : statusCurrentNodeClasses[s]

export const statusBadgeClasses: Record<NodeStatus, string> = {
  Integer: "bg-bnb-status-integer",
  Branched: "bg-bnb-status-branched",
  Pruned: "bg-bnb-status-pruned",
  Infeasible: "bg-bnb-status-infeasible",
}

export const neutralBadgeClass = "bg-muted"
export const statusBadgeClass = (s: NodeStatus | null) =>
  s === null ? neutralBadgeClass : statusBadgeClasses[s]
