import type { EdgeData, NodePosition } from "@/types/api-types"

export type TourSvgProps = {
  positions: NodePosition[] // run.instance.nodes
  edges: EdgeData[] // run.instance.edges
  values: number[] // edge_fractions OR 0/1 edge_selection, edge-indexed
  mode: "lp" | "tour"
}

const FRACTION_TOL = 1e-6
// Longer bbox side maps to this many units — roughly one unit per rendered
// pixel at inspector card width. Raw instance coordinates span wildly
// (eil51 ~70 units, att48 ~30000), so absolute stroke/r values in raw units
// either fuse the whole drawing into a blob or vanish.
const TARGET = 240
// Padding in normalized units, so breathing room scales with the drawing.
const PAD = 12
const STROKE_TOUR = 2
const STROKE_INTEGRAL = 2.5
const STROKE_LP_BASE = 1
const STROKE_LP_RANGE = 3
const NODE_R = 6.5
const LABEL_FONT = 7.5
// Halo around id labels: background-colored stroke behind the fill
// (paintOrder stroke) keeps digits legible where they cross tour edges
// or sit close to a neighbor in clustered instances.
const LABEL_HALO = 2

export function TourSvg({ positions, edges, values, mode }: TourSvgProps) {
  // TSPLIB y-up → SVG y-down: negate once, then normalize to ~screen scale.
  const raw = positions.map((p) => ({ x: p.x, y: -p.y }))
  const xs = raw.map((p) => p.x)
  const ys = raw.map((p) => p.y)
  const minX = Math.min(...xs)
  const minY = Math.min(...ys)
  const w = Math.max(...xs) - minX
  const h = Math.max(...ys) - minY
  // Guard against a single node (max bbox side 0).
  const s = TARGET / Math.max(w, h, 1)

  const pts = new Map(
    raw.map((p, i) => [
      positions[i].id,
      { x: (p.x - minX) * s, y: (p.y - minY) * s },
    ])
  )

  return (
    <svg
      viewBox={`${-PAD} ${-PAD} ${w * s + 2 * PAD} ${h * s + 2 * PAD}`}
      preserveAspectRatio="xMidYMid meet"
      className="h-auto w-full"
      role="img"
    >
      {edges.map((e, i) => {
        const a = pts.get(e.u)
        const b = pts.get(e.v)
        const value = values[i] ?? 0
        if (!a || !b) return null
        // Edge tooltip: endpoints + weight, plus the LP fraction in lp mode.
        const tip =
          mode === "tour"
            ? `${e.u}–${e.v} · weight ${e.weight.toFixed(1)}`
            : `${e.u}–${e.v}: ${value.toFixed(2)} · weight ${e.weight.toFixed(1)}`
        if (mode === "tour") {
          if (value <= 0.5) return null
          return (
            <line
              key={i}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              className="stroke-primary"
              strokeLinecap="round"
              strokeWidth={STROKE_TOUR}
            >
              <title>{tip}</title>
            </line>
          )
        }
        // lp mode: mirrors backend SVG semantics
        // — integral-included: primary, full width; fractional: warning,
        //   width ∝ fraction; excluded: not drawn
        if (value <= FRACTION_TOL) return null
        if (value >= 1 - FRACTION_TOL) {
          return (
            <line
              key={i}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              className="stroke-primary"
              strokeLinecap="round"
              strokeWidth={STROKE_INTEGRAL}
            >
              <title>{tip}</title>
            </line>
          )
        }
        return (
          <line
            key={i}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            className="stroke-warning"
            strokeLinecap="round"
            strokeWidth={STROKE_LP_BASE + STROKE_LP_RANGE * value}
          >
            <title>{tip}</title>
          </line>
        )
      })}
      {positions.map((p) => {
        const pt = pts.get(p.id)!
        return (
          <g key={p.id}>
            <circle
              cx={pt.x}
              cy={pt.y}
              r={NODE_R}
              className="fill-background stroke-foreground"
              strokeWidth={1}
            >
              <title>{p.id}</title>
            </circle>
            <text
              x={pt.x}
              y={pt.y}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={LABEL_FONT}
              className="fill-foreground stroke-background"
              strokeWidth={LABEL_HALO}
              paintOrder="stroke"
            >
              {p.id}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
