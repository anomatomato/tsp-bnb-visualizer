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
4. **Type Safety**: Backend export models (Pydantic) are the single source of truth; `just types` generates `frontend/src/types/api-types.ts` from them (pydantic2ts → json2ts). The generated file is committed and never hand-edited.
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
│  TSPBnb ── NodeFactory ── LPRelaxation (HiGHS)               │
│    │        │            └── CutPool (shared, subtour SECs)  │
│    │        └── BranchingStrategy (most-fractional default)  │
│    ├── OpenNodeQueue (best-bound | BFS | DFS priority)       │
│    ▼                                                         │
│  ProgressTracker (owns iteration numbering)                  │
│        │  callbacks                                          │
│    ┌───┴────────────────┐                                    │
│    ▼                    ▼                                    │
│  BnBSerializer      console progress table                   │
│    │  kamada-kawai positions (exported in JSON)              │
│    │  renderer (matplotlib SVGs, off unless render_svgs)     │
│    ▼                                                         │
│  output/runs/run_{instance}_{timestamp}/                     │
│    ├── bnb_state.json      ← complete replayable state       │
│    ├── index.html          ← fallback links page             │
│    └── images/             ← only with render_svgs=True      │
│                                                              │
│  export/viewer.py: detached localhost server +               │
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
│  Header: run picker · solver-config summary · theme toggle   │
│  ┌────────────────────────────────────────────┬───────────┐  │
│  │  BnB tree canvas (React Flow + dagre LR/TB)│ Inspector │  │
│  │  custom nodes: status color, LB label      │ outcome,  │  │
│  │  compact hover tooltip, legend             │ branching,│  │
│  │  dim nodes not yet reached by the replay   │ TourSvg × │  │
│  ├────────────────────────────────────────────┤ 3, dist.  │  │
│  │  Timeline: slider + play/pause             │ matrix    │  │
│  └────────────────────────────────────────────┴───────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Project Structure (actual)

```
tsp-bnb-visualizer/
├── pyproject.toml              # uv config; pytest/pyrefly/ruff settings
├── justfile                    # setup, example, publish, serve, types, clean, …
├── lefthook.yml                # git hooks: pre-commit + frontend eslint/prettier
├── tsp_bnb/                    # algorithm package (TSP-specific)
│   ├── bnb.py                  # TSPBnb — main search loop
│   ├── bnb_nodes.py            # NodeFactory — creates nodes, solves LPs
│   ├── relaxation.py           # Relaxation base + LPRelaxation (HiGHS modelling API)
│   ├── cut_pool.py             # CutPool — shared subtour-elimination cuts
│   ├── relaxed_solution.py     # RelaxedSolution (Pydantic, edge fractions)
│   ├── branching_decisions.py  # BranchingDecisions (edge-index fixations)
│   ├── branching_strategy.py   # BranchingStrategy + first-undecided/first-/most-fractional
│   ├── open_nodes.py           # OpenNodeQueue (heapq) + priority policies, PolicyInfo
│   ├── heuristics.py           # NearestNeighborHeuristic, TwoOptImproved
│   ├── solution_pool.py        # SolutionPool — incumbent tracking (min cost)
│   ├── progress_tracker.py     # ProgressTracker — iteration numbering, events
│   ├── data_schema.py          # TSPInstance, TSPSolution (Pydantic)
│   ├── _utils.py               # cycle ↔ edge-selection helpers
│   └── export/
│       ├── models.py           # Pydantic export models → bnb_state.json
│       ├── renderer.py         # matplotlib/networkx SVG rendering (opt-in)
│       ├── serializer.py       # BnBSerializer — run dir, JSON, index.html
│       └── viewer.py           # detached localhost server (psutil) + runs/index.json
├── examples/
│   ├── tsplib.py               # TSPLIB archive loader (EUC_2D gate)
│   └── data/                   # ALL_tsp.tar.gz TSPLIB archive
├── scripts/generate_types.py   # Pydantic export models → frontend/src/types/api-types.ts
├── tests/                      # pytest (+hypothesis): cut pool, relaxation,
│                               #   node outcomes, TSPLIB loader
├── frontend/                   # React + Vite + pnpm (see below)
├── output/                     # published viewer (tracked) + runs/ (ignored)
├── main.py                     # TSPLIB runner: registry, CLI (uv run main.py)
└── AGENTS.md / CLAUDE.md       # agent conventions (CLAUDE.md imports AGENTS.md)
```

### Frontend structure

```
frontend/src/
├── main.tsx                    # root: ThemeProvider + App
├── app/
│   ├── index.tsx               # AppShell: header + resizable tree | inspector
│   └── provider.tsx            # RunProvider, Suspense/ErrorBoundary, IterationProvider
├── context/
│   ├── run-context.tsx         # catalog + selected run (React state ↔ ?run= URL)
│   └── iteration-context.tsx   # current replay iteration (inspected node derives from it)
├── types/api-types.ts          # GENERATED from export/models.py (`just types`)
├── lib/                        # pure helpers, no React
│   ├── bnb.ts                  # tree flattening, React Flow mapping, outcomes, incumbentAt
│   ├── layout.ts               # dagre layoutTree (LR/TB toggle)
│   ├── run.ts                  # catalog + run fetching (cached promises)
│   ├── format.ts / status.ts   # solver-config/date formatting, status classes
├── components/                 # shared, domain-neutral (+ ui/ for shadcn)
├── hooks/                      # small generic hooks
└── features/                   # one folder per screen area
    ├── header/                 # run picker, solver-config summary + tooltip
    ├── tree/                   # React Flow canvas, node/edge types, legend,
    │                           #   timeline + usePlayback
    └── inspector/              # node header, branch decisions, outcome,
                                #   fractional edges, Solutions (TourSvg), distance matrix
```

Rules: dependencies point downward only (`features/tree/` → `lib/`, `components/`, `context/`), never sideways (`features/tree/` ↛ `features/inspector/`); state shared across areas (selected run, current iteration) lives in `context/`. Path alias `@/` → `src/`. Theming: shadcn CSS-variable tokens in `index.css` (`:root` / `.dark` + `@theme inline`), toggled by `components/theme-provider.tsx` (light/dark/system); React Flow gets `colorMode={resolvedTheme}`.

Run loading: `lib/run.ts` keeps one cached promise per run ID, consumed with React 19 `use()` under `Suspense` + an error boundary. Runs are immutable, so no React Query or invalidation is needed; catalog refreshes never evict cached runs. Run switches use `startTransition` so the current view stays visible while the next run loads.

---

## Backend Design

### Search loop (`tsp_bnb/bnb.py`)

`OpenNodeQueue` (heapq) with a pluggable priority function: `best_bound_order` (default, `(lower_bound, depth)`), `breadth_first_order`, `depth_first_order`. Branching-variable choice (`BranchingStrategy`) is independent of the search order. Per node: LP relaxation + lazy subtour cuts until integral or cut limit; prune when node LB ≥ incumbent; global termination when min open-node LB ≥ incumbent UB. Root is warm-started with NN + 2-opt heuristics (`TwoOptImproved`). Disconnected integral solutions are marked infeasible, not branched.

Key constraints (see AGENTS.md "Critical landmines" for details): `h.qsum` for expressions; one `LPRelaxation` per node, global `CutPool`, basis warm-starting; subtour cut violated when `cut_value < 2 - tol`; `BranchingDecisions` uses edge indices, not `(u, v)` tuples.

### Export (`tsp_bnb/export/`)

- `ProgressTracker` owns iteration numbering; `BnBSerializer` receives iteration values via callbacks (no duplicate counters).
- One deterministic weight-aware position set (`kamada_kawai_layout`, needs SciPy) is computed once and exported as `InstanceData.nodes`; the frontend draws every tour/LP solution from it.
- Backend SVG rendering is **off by default** (`BnBSerializer(instance, render_svgs=False)`); the matplotlib renderer stays intact and `render_svgs=True` re-enables it. All `image_path` fields are then `null`. SVG semantics when on: LP = red fractional edges + blue integral-included, width ∝ fraction; tours = blue.
- `serializer.save(open_browser=..., solver_config=...)` writes `bnb_state.json` + `index.html`; with `open_browser=True` it then runs the viewer sequence (see Data Flow). `open_browser=False` has no viewer side effects. `images/` is created lazily on first render.
- Partial runs: `TSPBnb.search()` raises `IterationLimitReached` (a `ValueError`) at the limit. The incumbent stays in `bnb.solutions` and the serializer has every event so far, so `main.py` still exports; undecided nodes stay open (`status: null`) and no global prune is recorded.

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
├── iterations: IterationEntry[]     # one per processed iteration (index = iteration - 1)
│   ├── node_id                     # node processed in this iteration
│   ├── global_lb                   # queue-wide LB after the iteration (null = queue empty)
│   ├── node_lb                     # processed node's own LP bound (null = LP infeasible)
│   ├── incumbent                   # best tour cost after the iteration
│   └── global_pruned_node_ids      # leftovers pruned here (only the final entry)
├── processing_order: [node_id, ...]          # slider position → processed node
├── started_at?                     # tz-aware ISO-8601 run start
└── solver_config                   # per component: identifier, short *_label, long *_description
                                    # (search_policy, branching_strategy, relaxation, root_heuristics)
```

Node-outcome semantics: `prune_reason` distinguishes per-node bound prunes
(processed nodes whose own LP bound lost to the incumbent) from global-bound
leftovers (queue nodes pruned together when the queue-wide minimum bound
certified optimality). `infeasible_reason` distinguishes an unsolvable LP
(`lp_infeasible`, fixations conflict with degree constraints) from an integral
but disconnected solution (`subtours`). `solver_config` records which strategy
components produced the run; the header shows the short labels and a tooltip
with the descriptions and identifiers. Display text is owned by the implementing
code: `PolicyInfo` in `open_nodes.py` for search policies, `display_name` /
`display_description` class variables on the strategy, relaxation, and
heuristic base classes.

`iterations` is derivable from the tree but exported anyway as convenient,
self-contained convergence data (GlobalLB vs incumbent per iteration). Global
pruning reuses the last processed iteration number, so leftovers are appended
to the final entry instead of creating a new one. `fixed_edges` together with a
parent's `branched_edge` gives the child's branch side directly.

Schema changes need no backward compatibility: old runs in `output/runs/` can be wiped (`just clean`) and regenerated.

---

## Frontend Design

| Decision         | Choice                                                 | Why                                                                                                                            |
| ---------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Framework        | React 19 + TypeScript                                  | mature ecosystem, strong tooling                                                                                               |
| Build            | Vite + pnpm                                            | fast, standard                                                                                                                 |
| Flow canvas      | **React Flow** (`@xyflow/react` v12)                   | nodes/edges/zoom/tooltips/minimap out of the box; React-idiomatic; MIT core covers all needs                                   |
| Tree layout      | **dagre** (`@dagrejs/dagre`)                           | sync, simple, `rankdir` flips horizontal/vertical                                                                              |
| UI library       | **shadcn/ui (Base UI) + Tailwind v4**                  | component source in repo, fully customizable; Slider/Table/Resizable cover the dashboard                                       |
| Per-node visuals | **`TourSvg`** (plain SVG in React)                     | positions already in JSON; normalized geometry, edge tooltips, per-card label toggle                                           |
| Backend SVGs     | opt-in only (`render_svgs=True`)                       | kept as a fallback/showcase artifact; dominated runtime + disk on bigger instances                                             |
| Run data         | fetched at runtime from `/runs` (no bundled fixture)   | one build serves every run; dev server mounts `output/runs` via middleware                                                     |
| Node appearance  | circle: LB label + status color; compact hover tooltip | details live in the inspector; nodes not yet reached by the replay are dimmed                                                  |
| Inspector        | one scrollable column of collapsible `Section`s        | Relaxed + playback-aware Incumbent always shown, Heuristic when present; container-query grid puts them side by side when wide |

React Flow conventions in this project: `nodeTypes`/`edgeTypes` maps at module scope (never inline); invisible 1×1px handles (edges anchor to handle box edges by design); `fitView` + `requestAnimationFrame(() => fitView())` after relayout. Wide tables (distance matrix) use one parent-owned scroll container; the vendored `Table` has no own overflow wrapper so sticky headers/columns resolve correctly.

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
     (bnb_state.json, index.html, images/ only with render_svgs)
  2. ensure detached viewer server (localhost:8123, PID in output/.server.pid)
  3. regenerate runs/index.json   (newest-first catalog, atomic write)
  4. open browser tab   http://localhost:8123/?run={run_id}
```

Invariant: when a tab loads `?run=<id>`, `<id>` is already in the catalog — the catalog is written between "run dir complete" and "tab opens", never before.

- Viewer publishing is manual: `just publish` builds the frontend and copies `frontend/dist` (`index.html` + `assets/`) into `output/`. That build is **tracked in git** (`.gitignore` re-includes `output/index.html`, `output/assets/`, `output/*.svg`), so a fresh clone can view runs without Node. After any frontend change: `just publish`, then commit `output/`. If no published viewer exists, `save()` opens the run-local stub `index.html` instead.
- Port: `BNB_VIEWER_PORT` (default 8123). The server binds to localhost only. Process management uses psutil, so it works on Linux, macOS, and Windows; logs go to `output/.server.log`.
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
11. **Runtime-loaded runs** (2026-10): one published viewer + `runs/index.json` catalog + `?run=` URL, instead of one frontend build per run. Detached stdlib `http.server` (psutil lifecycle); Flask only if the server ever needs to mutate state.
12. **Codegen types** (2026-10): Pydantic export models → `api-types.ts` via `just types`; no hand-mirrored TypeScript.
13. **Explicit outcome metadata** (2026-10): `prune_reason`, `infeasible_reason`, `branched_edge`, `pruned_at`, `iterations[]` exported rather than inferred in the frontend.
14. **Frontend-rendered tours** (2026-10): `TourSvg` replaced backend SVG images; backend rendering kept but off by default.
15. **Root `main.py` runner** (2026-10): typed `Tier` registry of EUC_2D TSPLIB instances; the loader rejects other edge-weight types (`ATT` optima would be compared against wrong weights).

---

## Tooling

- **Python**: uv (`uv sync`, `uv run pytest`, `uv run pyrefly check`, `uv run ruff check --fix`), pre-commit hooks (pyrefly, ruff, prettier, blacken-docs, shellcheck, uv-lock, uv-export, name-tests-test, disallow-caps).
- **Git hooks**: Lefthook (`lefthook.yml`) runs pre-commit on staged files plus frontend `eslint --fix` / `prettier --write` (auto-staged on success). Installed by `just setup`.
- **Frontend**: pnpm (`dev`, `build`, `typecheck` = `tsc -b`, `lint`, `format`), ESLint + typescript-eslint + jsx-a11y + tailwindcss, React Compiler (babel-plugin-react-compiler).
- **Type pipeline**: `just types` → `scripts/generate_types.py` (pydantic2ts, needs `json2ts` on `PATH`) → `frontend/src/types/api-types.ts`, committed, never hand-edited.
- **Task runner**: `justfile`. See README for the command table.

---

_Last updated: 2026-10-27_
_Project: TSP BnB Visualizer_
