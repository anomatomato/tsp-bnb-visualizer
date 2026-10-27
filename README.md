# TSP BnB Visualizer

Research tool for visualizing a **TSP Branch-and-Bound** solver: HiGHS LP relaxation, lazy subtour-elimination cutting planes, most-fractional branching — and a React frontend that replays the search iteration by iteration.

Static-only by design: the backend writes a complete, replayable run directory.

## Repository layout

| Path              | What                                                         |
| ----------------- | ------------------------------------------------------------ |
| `main.py`         | TSPLIB runner (default `eil51` + `st70`; `--list` for more)  |
| `tsp_bnb/`        | BnB algorithm package (Python + HiGHS + NetworkX)            |
| `tsp_bnb/export/` | Static export: `bnb_state.json`, optional SVGs, `index.html` |
| `examples/`       | TSPLIB loader (EUC_2D only) + archive                        |
| `frontend/`       | React 19 + Vite + React Flow visualizer (pnpm)               |
| `tests/`          | pytest + hypothesis                                          |
| `output/`         | Generated run artifacts (gitignored)                         |

Design docs: [`ARCHITECTURE.md`](ARCHITECTURE.md) · roadmap and status: [`PLAN.md`](PLAN.md) · agent conventions: [`AGENTS.md`](AGENTS.md)

## Backend quickstart

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # install deps
uv run main.py                   # solve eil51 + st70, export + open browser
uv run main.py --list            # registry: warm-up / medium / big instances
uv run main.py pcb442 --limit 300   # stress probe; partial run still exported
uv run main.py kroA200 --no-export  # timing only, no artifacts
```

Output lands in `output/runs/run_eil51_<timestamp>/`:

- `bnb_state.json` — complete replayable state (tree with per-node LP/heuristic snapshots, incumbent timeline, processing order, city positions)
- `images/` — per-node SVGs, only with `BnBSerializer(instance, render_svgs=True)`
- `index.html` — links to everything

Other useful commands:

```bash
uv run pytest                  # tests
uv run pyrefly check           # type check
uv run ruff check --fix        # lint
uv run pre-commit run --all-files
```

## Frontend quickstart

Requires Node 22 + pnpm (see `mise.toml`).

```bash
cd frontend
pnpm install
pnpm dev                       # Vite dev server
```

During development the app runs on a frozen run fixture (`src/mock/eil51-bnb-state.json` — copy a fresh `bnb_state.json` from a backend run)..md` for the frontend roadmap.

## Verified results

- `eil51`: solved to the known optimum (426.0) in 39 BnB iterations.
- `st70`: part of the default `uv run main.py` run.
- TSPLIB loading is restricted to EUC_2D (Euclidean) instances.
