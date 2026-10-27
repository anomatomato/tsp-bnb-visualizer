# TSP BnB Visualizer


https://github.com/user-attachments/assets/ac937034-f02f-49fe-ad2f-98806e28d89e


A research tool for visualizing **TSP Branch-and-Bound**. The Python backend solves TSP with HiGHS LP relaxations, lazy subtour-elimination cuts and most-fractional branching. It records every iteration, and the React frontend replays the search tree step by step.

Each solver run writes a self-contained run directory in `output/`, and the viewer `output/index.html` loads it afterwards.

## Requirements

| Tool                                              | Needed for                             |
| ------------------------------------------------- | -------------------------------------- |
| Python 3.14+ and [uv](https://docs.astral.sh/uv/) | running the solver (always)            |
| [just](https://just.systems/)                     | the shortcut commands below (optional) |
| Node 22 and pnpm (see `mise.toml`)                | only for changing the frontend         |

A pre-built viewer already exists in `output/` (`index.html` and `assets/`), so **you can view solves without installing Node**.

## Quickstart

```bash
just setup        # uv sync + lefthook hooks + pnpm install (skip pnpm if you are not developing the frontend: `just install`)
just example      # solve eil51, st70, rat99 → export → open the viewer in the browser
```

Without `just`:

```bash
uv sync
uv run main.py
```

Each solve writes `output/runs/run_<instance>_<timestamp>/`. It then starts a detached viewer server on <http://localhost:8123> (or reuses one that is already running) and opens a tab at `?run=<run-id>`. The run picker in the header lists every run in `output/runs/`.

## `just` commands

Run `just --list` to see every recipe. These are the important ones:

| Command                          | What it does                                                                                                                                                                                                     |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `just setup` (`just s`)          | Install Python deps (all groups), Lefthook git hooks and frontend deps.                                                                                                                                          |
| `just install`                   | Python deps only, if you do not need the frontend toolchain.                                                                                                                                                     |
| `just example [ARGS]` (`just e`) | Run the TSPLIB runner and pass `ARGS` through to `main.py` (see below).                                                                                                                                          |
| `just publish`                   | **Build the frontend and copy it into `output/`.** Run this after every frontend change, otherwise the viewer server keeps serving the old build. Commit the resulting `output/index.html` and `output/assets/`. |
| `just serve`                     | Start or reuse the detached viewer server, refresh the run catalog and print the URL.                                                                                                                            |
| `just serve-stop`                | Stop the viewer server. Only stops the PID it started itself; it is safe to run twice.                                                                                                                           |
| `just test` (`just t`)           | Run `pytest`.                                                                                                                                                                                                    |
| `just types`                     | Regenerate `frontend/src/types/api-types.ts` from the Pydantic export models. Needs `json2ts` on `PATH` (`pnpm add -g json-schema-to-typescript`).                                                               |
| `just clean` (`just c`)          | Delete all runs in `output/runs/` and write an empty catalog.                                                                                                                                                    |
| `just update-all` (`just u`)     | Update pre-commit hooks, Python and frontend deps. Each part commits its own lockfile changes.                                                                                                                   |

## Running instances

`main.py` holds a registry of EUC_2D TSPLIB instances in three tiers (warm-up, medium, big). Each entry stores its known optimum and an iteration limit.

```bash
uv run main.py --list                  # registry grouped by tier
uv run main.py berlin52 kroA100        # explicit instances, in this order
uv run main.py pcb442 --limit 300      # override the iteration limit
uv run main.py kroA200 --no-export     # timing run: no serializer, no artifacts
uv run main.py eil51 --no-browser      # export, but do not start a server or open a tab
```

- A run that reaches its iteration limit still exports a valid partial run. The log reports the incumbent and its gap to the optimum, and nodes that were never processed stay "in the open queue" in the viewer.
- Comparisons with the known optimum are only logged; they do not fail the run.
- The loader (`examples/tsplib.py`) rejects every instance that is not `EUC_2D`, because the optima of `ATT`/`GEO` instances use a different distance function.
- Big instances are slow. The LP covers the complete graph, so `pcb442` needs about two minutes for ten iterations.

Reference results (best-bound search, default limits):

| Instance | Iterations | Result        |
| -------- | ---------- | ------------- |
| eil51    | 39         | optimum 426   |
| st70     | 12         | optimum 675   |
| rat99    | 17         | optimum 1211  |
| kroA100  | 543        | optimum 21282 |

- `examples/demo_run.py` demonstrates how to define custom instances and visualize them.

## What a run directory contains

```
output/
├── index.html, assets/          # published viewer (just publish), tracked in git
├── runs/
│   ├── index.json               # run catalog, newest first (regenerated by the solver / just serve)
│   └── run_eil51_<timestamp>/
│       ├── bnb_state.json       # complete replayable state: tree, LP snapshots, incumbents, iterations
│       └── index.html           # fallback page with links to the JSON (and images, if any)
├── .server.pid, .server.log     # viewer server bookkeeping
```

The backend does not write SVGs by default, because the frontend draws tours and LP solutions itself. Pass `BnBSerializer(instance, render_svgs=True)` to get the matplotlib SVGs in `images/`, right now they are still unused in the frontend.

The viewer port defaults to 8123. Set `BNB_VIEWER_PORT` to use a different one.

## Repository layout

| Path              | What                                                            |
| ----------------- | --------------------------------------------------------------- |
| `main.py`         | TSPLIB runner: instance registry and CLI                        |
| `tsp_bnb/`        | BnB solver package (HiGHS, NetworkX, Pydantic)                  |
| `tsp_bnb/export/` | Export models, serializer, optional SVG renderer, viewer server |
| `examples/`       | TSPLIB loader and the TSPLIB archive (`data/`)                  |
| `frontend/`       | React 19 + Vite + React Flow viewer                             |
| `scripts/`        | `generate_types.py` (Pydantic → TypeScript)                     |
| `tests/`          | pytest + hypothesis                                             |
| `output/`         | Published viewer (tracked) and run artifacts (ignored)          |

Further reading: [`ARCHITECTURE.md`](ARCHITECTURE.md) for the design and data format, and [`AGENTS.md`](AGENTS.md) for conventions and pitfalls (`CLAUDE.md` imports it).

## Frontend development

```bash
pnpm -C frontend install
pnpm -C frontend dev          # Vite dev server with HMR
```

The dev server serves the real `output/runs/` through a small `/runs` middleware, so it shows the same runs as the published viewer and no Python server is needed. You have to produce runs with `uv run main.py` first.

When you are done: run `just publish` and commit `output/`. See [`frontend/README.md`](frontend/README.md) for the frontend layout and conventions.

## Checks

```bash
uv run pytest                         # backend tests
uv run pyrefly check                  # type check (pyrefly, not mypy)
uv run ruff check --fix && uv run ruff format
pnpm -C frontend typecheck            # tsc -b
pnpm -C frontend lint
uv run pre-commit run --all-files     # everything the git hook runs
```

Lefthook runs pre-commit and the frontend ESLint/Prettier on staged files at commit time.
