# Frontend: BnB viewer

This is the React 19 + TypeScript + Vite app that replays a run exported by the Python solver. It uses React Flow (`@xyflow/react`) for the tree and dagre for the layout. The UI is built with shadcn/ui on Base UI and Tailwind v4, and the React Compiler is enabled.

The app does not bundle any run data. At runtime it fetches `/runs/index.json` (the catalog) and `/runs/<run-id>/bnb_state.json`, and the active run is selected with `?run=<run-id>`.

## Commands

Requires Node 22 and pnpm (see the root `mise.toml`). Run these from the repo root with `-C frontend`, or from inside `frontend/`:

```bash
pnpm -C frontend install
pnpm -C frontend dev         # dev server; serves ../output/runs at /runs
pnpm -C frontend build       # tsc -b + vite build → frontend/dist
pnpm -C frontend typecheck   # tsc -b
pnpm -C frontend lint        # ESLint (jsx-a11y, tailwindcss, react-hooks)
pnpm -C frontend format      # Prettier (+ tailwind class sorting)
```

**After a change, publish the build:** `just publish` from the repo root. It builds the app and copies `dist/` into `output/`, where the detached viewer server (`localhost:8123`) serves it. Commit the updated `output/index.html` and `output/assets/`; that tracked build is what users get without Node.

The `typecheck` script must stay `tsc -b`. The root `tsconfig.json` is solution-style (`files: []` plus references), so a bare `tsc --noEmit` checks nothing and always passes.

## Data and types

- `src/types/api-types.ts` is **generated** from `tsp_bnb/export/models.py`. Do not edit it by hand; run `just types` (needs `json2ts` on `PATH`).
- In dev mode, the custom `serve-output-runs` middleware in `vite.config.ts` serves `../output/runs`. Generate runs with `uv run main.py` before you start the dev server.

## Layout (`src/`)

```
main.tsx                     # root: ThemeProvider + App
app/
  index.tsx                  # AppShell: header + resizable tree | inspector
  provider.tsx               # RunProvider, Suspense/ErrorBoundary, IterationProvider
context/
  run-context.tsx            # run catalog + selected run (state ↔ ?run= URL)
  iteration-context.tsx      # current replay iteration; the inspected node is derived from it
features/
  header/                    # run picker, solver-config summary + tooltip, theme toggle
  tree/                      # React Flow canvas, custom node/edge, legend, timeline, playback
  inspector/                 # node header, branch decisions, outcome, fractional edges,
                             # solutions (TourSvg: relaxed / incumbent / heuristic), distance matrix
lib/                         # pure helpers: bnb.ts (tree mapping, outcomes, incumbentAt), layout.ts
                             # (dagre), run.ts (fetching), format.ts, status.ts (status classes)
components/                  # shared: theme provider, loading/error screens, ui/ (shadcn)
hooks/                       # small generic hooks
```

Dependencies only point downwards: `features/*` may import from `lib/`, `components/` and `context/`, but never from another feature. State that several areas need lives in `context/`.

## Conventions

- Path alias `@/` → `src/`. It is configured in **both** `tsconfig.app.json` and `vite.config.ts`.
- React Flow `nodeTypes`/`edgeTypes` are defined at module scope, never inline.
- In code we write ourselves, use only these spacing/sizing steps: `1 2 3 4 6 8 12 16 24 32 48 64 96 128 160 192`. Opacity modifiers come only from `10 20 30 50 80`. Meaningful colors are tokens (`--bnb-status-*`, `--warning`) with a `.dark` twin. The full rules are in the root `ARCHITECTURE.md`.
- Use named exports for new modules.
- Adding a shadcn component: `pnpm -C frontend dlx shadcn@latest add <name>`. The source lands in `src/components/ui/`.
