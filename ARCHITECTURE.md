# TSP BnB Visualizer Architecture

## Overview

**Project**: TSP Branch-and-Bound Visualization Tool
**Purpose**: Research tool for visualizing a TSP Branch-and-Bound solver that uses **HiGHS** for LP relaxation, **lazy subtour elimination** cutting planes, and **most-fractional branching**.
**Scope**: **Static visualization only** — the backend writes a complete, replayable run directory; no live/WebSocket mode (dropped from scope).
**Target Users**: Researchers and students studying how BnB explores the search tree

---

## Core Principles

1. **Separation of Concerns**: Backend (Python + HiGHS) computes and exports; frontend (React + React Flow) renders and interacts. They share exactly one artifact: `bnb_state.json`.
2. **TSP-Specific**: A TSP BnB solver, not a generic framework.
3. **Maintainability**: React + React Flow + **shadcn/ui** — component source lives in the repo, no library black boxes.
4. **Type Safety**: Backend export models (Pydantic) mirrored by hand-written TypeScript types now; Pydantic → JSON Schema → TS codegen once the models stabilize.
5. **Visualization-first**: the BnB backend follows the classic best-bound search template; the bigger engineering effort goes into the visualizer.
6. **Replayable Export**: Every BnB iteration is reconstructable in the frontend from the exported state — node creation/processing iterations, LP solutions, incumbent timeline.

---

## System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  BACKEND (Python, uv)                                        │
│                                                              │
│  TSPInstance (nx.Graph)                                      │
│        │                                                     │
│        ▼                                                     │
│  TSPBnb ── NodeFactory ── LPRelaxationSolver (HiGHS)         │
│    │        │            └── CutPool (shared, subtour SECs)  │
│    │        └── most-fractional branching                    │
│    ▼                                                         │
│  ProgressTracker (owns iteration numbering)                  │
│        │  callbacks                                          │
│    ┌───┴────────────────┐                                    │
│    ▼                    ▼                                    │
│  BnBSerializer      console progress table                   │
│    │  renderer (matplotlib + networkx,                       │
│    │           kamada-kawai positions)                       │
│    ▼                                                         │
│  output/runs/run_{instance}_{timestamp}/                     │
│    ├── bnb_state.json      ← complete replayable state       │
│    ├── index.html          ← links (JSON + images)           │
│    └── images/                                                │
│        ├── relaxation_{node}.svg   (LP fractions)            │
│        └── tour_{node}.svg         (incumbent/heuristic)     │
│                                                              │
│  export/viewer.py: detached localhost server +              │
│  runs/index.json catalog (save order: run dir → server →     │
│  catalog → browser tab)                                      │
└──────────────────────────────────────────────────────────────┘
                        │
                        │  http://localhost:8123/?run={id}
                        │  (dev: Vite /runs middleware)
                        ▼
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND (React 19 + Vite + pnpm, in frontend/)             │
│                                                              │
│  App shell (shadcn/ui + Tailwind, Resizable panels)          │
│  ┌────────────────────────────────────────────┬───────────┐  │
│  │  BnB tree canvas (React Flow + dagre LR)   │ Inspector │  │
│  │  custom nodes: status color, LB label      │ (node     │  │
│  │  tooltip: full detail on hover/focus       │  details, │  │
│  │  dim+disable unprocessed nodes per slider  │  backend  │  │
│  │                                            │  SVGs)    │  │
│  ├────────────────────────────────────────────┴───────────┤  │
│  │  Timeline: iteration slider + play/pause + bounds table │  │
│  └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Project Structure (actual)

```
tsp-bnb-visualizer/
├── pyproject.toml              # uv config; pytest/pyrefly/ruff settings
├── tsp_bnb/                    # algorithm package (TSP-specific)
│   ├── bnb.py                  # TSPBnb — main search loop
│   ├── bnb_nodes.py            # NodeFactory — creates nodes, solves LPs
│   ├── relaxation.py           # LPRelaxationSolver (HiGHS modelling API)
│   ├── cut_pool.py             # CutPool — shared subtour-elimination cuts
│   ├── relaxed_solution.py     # RelaxedSolution (Pydantic, edge fractions)
│   ├── branching_decisions.py  # BranchingDecisions (edge-index fixations)
│   ├── branching_strategy.py   # MostFractionalBranchingStrategy
│   ├── open_nodes.py           # OpenNodeContainer (heapq, best-bound default)
│   ├── heuristics.py           # NearestNeighborHeuristic, TwoOptImproved
│   ├── solution_pool.py        # SolutionPool — incumbent tracking (min cost)
│   ├── progress_tracker.py     # ProgressTracker — iteration numbering, events
│   ├── data_schema.py          # TSPInstance, TSPSolution (Pydantic)
│   ├── _utils.py               # cycle ↔ edge-selection helpers
│   └── export/
│       ├── models.py           # Pydantic export models → bnb_state.json
│       ├── renderer.py         # matplotlib/networkx SVG rendering
│       └── serializer.py       # BnBSerializer — run dir, JSON, index.html
├── examples/
│   ├── tsplib.py               # TSPLIB archive loader (EUC_2D gate)
│   └── data/                   # ALL_tsp.tar.gz TSPLIB archive
├── tests/                      # pytest (+hypothesis): test_cut_pool, test_relaxation
├── frontend/                   # React + Vite + pnpm (see below)
├── output/                     # gitignored run artifacts
└── main.py                     # TSPLIB runner: registry, CLI (uv run main.py)
```

### Frontend structure (target)

```
frontend/src/
├── main.tsx / App.tsx          # shell: layout + shared state wiring
├── types/bnb.ts                # backend model types (hand-written → codegen later)
├── mock/eil51-bnb-state.json   # frozen run fixture for development
├── lib/
│   ├── bnb.ts                  # mapper: BnBState → React Flow nodes/edges
│   └── layout.ts               # dagre layoutTree (LR/TB toggle)
├── components/                 # shared, domain-neutral (+ ui/ for shadcn)
├── features/                   # one folder per screen area
│   ├── tree/                   # React Flow canvas area (custom node, edges)
│   ├── timeline/               # iteration slider + play/pause + bounds table
│   └── inspector/              # node details sidebar (backend SVGs)
└── (theme-provider.tsx lives in components/)
```

Rules: dependencies point downward only (`features/tree/` → `lib/`, `components/`), never sideways (`features/tree/` ↛ `features/inspector/`); state shared across areas (selected node, current iteration) lives in `App.tsx` or a context. Path alias `@/` → `src/`. Theming: shadcn CSS-variable tokens in `index.css` (`:root` / `.dark` + `@theme inline`), toggled by `components/theme-provider.tsx` (light/dark/system); React Flow gets `colorMode={resolvedTheme}`.

---

## Backend Design

### Search loop (`tsp_bnb/bnb.py`)

Best-bound search (`OpenNodeContainer`, heapq, `(lower_bound, depth)` order). Per node: LP relaxation + lazy subtour cuts until integral or cut limit; prune when node LB ≥ incumbent; global termination when min open-node LB ≥ incumbent UB. Root is warm-started with NN + 2-opt heuristics (`TwoOptImproved`). Disconnected integral solutions are marked infeasible, not branched.

Key constraints (see AGENTS.md "Critical landmines" for details): `h.qsum` for expressions; one `LPRelaxationSolver` per node, global `CutPool`, basis warm-starting; subtour cut violated when `cut_value < 2 - tol`; `BranchingDecisions` uses edge indices, not `(u, v)` tuples.

### Export (`tsp_bnb/export/`)

- `ProgressTracker` owns iteration numbering; `BnBSerializer` receives iteration values via callbacks (no duplicate counters).
- One deterministic weight-aware position set (`kamada_kawai_layout`, needs SciPy) reused across all renders.
- SVG semantics: LP = red fractional edges + blue integral-included, width ∝ fraction; tours = blue.
- `serializer.save()` writes `bnb_state.json` + `index.html` and auto-opens the browser. Directories are created lazily on first render.

### `bnb_state.json` format (`export/models.py`)

```
BnBRunData
├── instance: InstanceData          # name, nodes[{id,x,y}], edges[{u,v,weight}]
├── tree: NodeVisData (recursive)
│   ├── node_id, parent_id, depth
│   ├── lb                           # queue-wide global LB when the node's
│   │                               # fate was decided: at processing, or
│   │                               # the queue-wide bound that closed the
│   │                               # queue for globally pruned leftovers
│   │                               # (NOT the node's own bound — that is
│   │                               # relaxed_solution.objective)
│   ├── ub                           # incumbent when the node's fate was
│   │                               # decided: at processing, or at the
│   │                               # global-prune iteration for leftovers
│   ├── created_at, processed_at     # iteration numbers
│   ├── pruned_at                    # prune iteration (== processed_at for
│   │                               # node-bound prunes; global-prune iter
│   │                               # for queue leftovers)
│   ├── status: NodeStatus           # branched|integer|pruned|infeasible (None until decided)
│   ├── prune_reason?                # node_bound | global_bound (Pruned only)
│   ├── infeasible_reason?           # lp_infeasible | subtours (Infeasible only)
│   ├── branched_edge?               # edge index this node branched on (Branched only)
│   ├── relaxed_solution?: RelaxedSnapshot   # edge_fractions, objective, is_integral_tour, image_path
│   ├── heuristic_solution?: TourSnapshot     # edge_selection, cost, image_path
│   ├── fixed_edges: (0|1|null)[]    # per edge index: free/out/in
│   └── children: NodeVisData[]
├── best_solutions: [{iteration, cost, edge_selection, image_path}]
├── processing_order: [node_id, ...]          # slider position → processed node
├── started_at?                     # tz-aware ISO-8601 run start (None for pre-field runs)
└── solver_config                   # per component: identifier, short *_label, long *_description
                                    # (search_policy, branching_strategy, relaxation, root_heuristics)
```

Node-outcome semantics: `prune_reason` distinguishes per-node bound prunes
(processed nodes whose own LP bound lost to the incumbent) from global-bound
leftovers (queue nodes pruned together when the queue-wide minimum bound
certified optimality). `infeasible_reason` distinguishes an unsolvable LP
(`lp_infeasible`, fixations conflict with degree constraints) from an integral
but disconnected solution (`subtours`). `solver_config` records which strategy
components produced the run, so the frontend can later display them.

City positions are included in `InstanceData.nodes`, so the frontend can render tours/LP solutions itself if desired (optional `TourSvg`, see PLAN).

---

## Frontend Design

| Decision                 | Choice                                                                | Why                                                                                          |
| ------------------------ | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Framework                | React 19 + TypeScript                                                 | mature ecosystem, strong tooling                                                             |
| Build                    | Vite + pnpm                                                           | fast, standard                                                                               |
| Flow canvas              | **React Flow** (`@xyflow/react` v12)                                  | nodes/edges/zoom/tooltips/minimap out of the box; React-idiomatic; MIT core covers all needs |
| Tree layout              | **dagre** (`@dagrejs/dagre`)                                          | sync, simple, `rankdir` flips horizontal/vertical                                            |
| UI library               | **shadcn/ui + Tailwind**                                              | component source in repo, fully customizable; Slider/Table/Resizable cover the dashboard     |
| Flow styling             | React Flow UI components (optional)                                   | pre-styled shadcn-compatible nodes/tooltips/controls, installed per-piece via shadcn CLI     |
| Per-node visuals (v1)    | backend SVG images                                                    | zero frontend work, consistent with Python-side artifacts                                    |
| Per-node visuals (later) | `TourSvg` component (plain SVG in React)                              | positions already in JSON; interactive; replaces `<img>` when wanted                         |
| Dev data                 | frozen `mock/eil51-bnb-state.json`                                    | deterministic, offline, no server during frontend dev                                        |
| Node appearance          | circle: LB label + status color; tooltip on hover/focus = full detail | dim + disable unprocessed nodes per slider (fallback: hide)                                  |

React Flow conventions in this project: `nodeTypes`/`edgeTypes` maps at module scope (never inline); invisible 1×1px handles (edges anchor to handle box edges by design); custom `CircleEdge` (circle-intersection endpoints) once diagonal connections matter; `fitView` + `requestAnimationFrame(() => fitView())` after relayout.

### Spacing & sizing system

One shared scale for spacing **and** sizing decisions, following _Refactoring UI_ (Wathan & Schoger), "Establish a spacing and sizing system": a 16px base with multiplicative steps, so no two adjacent values are closer than roughly 25% and are therefore always visually distinguishable.

| px       | 4   | 8   | 12  | 16  | 24  | 32  | 48   | 64   | 96   | 128  | 192  | 256  | 384  | 512   | 640   | 768   |
| -------- | --- | --- | --- | --- | --- | --- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----- | ----- | ----- |
| Tailwind | `1` | `2` | `3` | `4` | `6` | `8` | `12` | `16` | `24` | `32` | `48` | `64` | `96` | `128` | `160` | `192` |

Rules:

- For paddings, margins, gaps, widths, and heights **in code we write ourselves**, use only this subset (`p-3`, `gap-6`, `w-64`, `size-16`, …). Values between the steps (`p-5`, `gap-14`, `w-[18px]`, …) exist in Tailwind but are not in the system — the scale is enforced by convention, not by the framework.
- shadcn components' internal fine-grained values (`gap-1.5`, `h-8`, `size-3.5`) belong to their own design system and stay untouched.
- Typography has a smaller perceptual floor — the 25% rule applies to spacing/sizing, not to the type scale.

### Color & opacity conventions

**Two layers.** shadcn's semantic tokens (`background`, `primary`, `destructive`, `muted`, …) cover all UI chrome. Tailwind's raw color ramps (`bg-emerald-600`, `text-amber-500`) are for one-off decoration only. A color that starts _meaning_ something (third use, or domain semantics) gets promoted to its own token with a `.dark` twin — see `--warning` for the pattern.

**Opacity vocabulary** (derive shades at use time, don't define shade tokens):

| Opacity        | Role                                                | Example                              |
| -------------- | --------------------------------------------------- | ------------------------------------ |
| `/10`–`/20`    | tinted container (soft surface, full-strength text) | `bg-destructive/10 text-destructive` |
| `/50` (+`/20`) | focus/attention ring                                | `focus-visible:ring-ring/50`         |
| `/80`          | hover state                                         | `hover:bg-primary/80`                |
| `/30`–`/70`    | de-emphasis steps                                   | `opacity-30` for dimmed nodes        |

Stick to this set (`10 20 30 50 80`) rather than arbitrary values. Alpha blends with the surface beneath, so one class works in light and dark mode.

**Anchor-strength rule:** every token is defined once at its strongest _needed_ value (full chroma, still legible as text on `--background`), and every softer variant is an opacity modifier of it. Never define a shade ramp as separate tokens.

**Dark-mode derivation:** same H, raise L (+0.08–0.12), cut C (~×0.6). Keep hue constant so a color reads as the same color in both themes.

**Categorical/status families** (e.g. `--bnb-status-*`): fix one L across all members (equal perceived brightness, none pops unfairly), sweep H per member; neutral members may alias existing tokens (`var(--muted-foreground)`).

**Data-visualization surfaces** (tree nodes): fill = status token at `/10`–`/20`, stroke = status token full strength, label text = `--foreground` (never the status color — readability first). SVG works with the same utilities: `fill-(--bnb-status-x)/20`, `stroke-(--bnb-status-x)`.

---

## Data Flow (static only)

```
uv run main.py [instances] [--limit N] [--no-browser] [--no-export]
        │
        ▼
search → serializer.save()   (owns the ordering)
  1. write output/runs/run_{instance}_{timestamp}/
     (bnb_state.json, images/, index.html)
  2. ensure detached viewer server (localhost:8123, PID in output/.server.pid)
  3. regenerate runs/index.json   (newest-first catalog, atomic write)
  4. open browser tab   http://localhost:8123/?run={run_id}
```

Invariant: when a tab loads `?run=<id>`, `<id>` is already in the catalog — the catalog is written between "run dir complete" and "tab opens", never before.

- Viewer publishing is manual: `just publish` copies `frontend/dist` (`index.html` + `assets/`) into `output/`. Until then, `save()` opens the run-local stub page instead.
- Server lifecycle: `just serve` (ensure/reuse + catalog refresh + URL), `just serve-stop` (stops only our tracked PID, never a foreign port occupant), or directly `python -m tsp_bnb.export.viewer [stop]`.
- Frontend dev (`pnpm dev`) serves `output/runs` live through the custom `/runs` Vite middleware — no Python server needed. The catalog is refreshed only by `save(open_browser=True)` and the `viewer` module entry; headless exports and manual deletions leave it stale until refreshed.
- `just clean` deletes all runs and regenerates an empty catalog.

Later (research workflow): the app can load arbitrary `bnb_state.json` files via file-picker/drag-drop — no server needed (each run carries `started_at` itself).

---

## Key Design Decisions (history)

1. **TSP-specific**, not a generic framework.
2. **HiGHS** LP + degree constraints, solved per node (no persistent shared model).
3. **Lazy subtour elimination** via external cut loop + shared `CutPool` (LP relaxations get no MIP callbacks).
4. **Most-fractional branching**; branching-variable choice independent of search order.
5. **NetworkX** graph input; **Python 3.14** + **uv**.
6. **Heuristic warm start** (NN + 2-opt) at root for initial UB.
7. **Static-only export** — live WebSocket mode dropped from scope (2026-08).
8. **React** (2026-09): mature ecosystem, strong tooling.
9. **React Flow over vanilla D3**: interaction feature list (zoom, tooltips, selection, minimap, replay) is RF's core competency; D3 would be hand-rolled imperative DOM alongside React. dagre still used as a pure math library for positions.
10. **shadcn/ui over Bootstrap**: owned component source, Tailwind styling, straightforward customization; Bootstrap lacks a slider and fights customization.

---

## Tooling

- **Python**: uv (`uv sync`, `uv run pytest`, `uv run pyrefly check`, `uv run ruff check --fix`), pre-commit (pyrefly, ruff, prettier, blacken-docs, shellcheck, uv-lock, name-tests-test, disallow-caps).
- **Frontend**: pnpm (`pnpm dev`, `pnpm build`, `pnpm lint`), ESLint + typescript-eslint, React Compiler (babel-plugin-react-compiler).
- **Type pipeline**: hand-written `types/bnb.ts` now; `pydantic2ts` (or JSON Schema + json-schema-to-typescript) once `export/models.py` stabilizes. Generated files are committed and marked auto-generated.

---

_Last updated: 2026-10-09_
_Project: TSP BnB Visualizer_
