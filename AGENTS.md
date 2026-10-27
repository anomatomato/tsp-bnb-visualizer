# AGENTS.md

Repository: TSP Branch-and-Bound visualizer (Python + HiGHS backend, React + React Flow frontend).
Read `ARCHITECTURE.md` and `PLAN.md` for the high-level design before starting.

## Setup

Python 3.14+. All Python package management via `uv` (lockfile is `uv.lock`).

```bash
uv sync                          # install deps + dev group
uv run pytest                    # run all tests
uv run pytest tests/test_xxx.py  # single test file
uv run pytest -k name            # by test name
uv run pyrefly check             # type check (pyrefly, NOT mypy)
uv run ruff check --fix          # lint
uv run ruff format               # format
uv run pre-commit run --all-files  # full pre-commit suite
```

Frontend: Node 22 (`mise.toml`), pnpm, lives in `frontend/`.

```bash
pnpm -C frontend install       # deps (node_modules)
pnpm -C frontend dev           # Vite dev server
pnpm -C frontend build         # tsc -b + vite build
pnpm -C frontend lint          # ESLint
pnpm -C frontend typecheck     # tsc --noEmit
```

`pyproject.toml` configures `pythonpath = ["tsp_bnb"]` and `search-path = ["tsp_bnb"]` for pytest / pyrefly / pyright — so tests and source files can `from tsp_bnb import ...` directly without an editable install.

## Critical landmines

### HiGHS APIs that bite

- Use `h.qsum(...)` not Python `sum()` for expressions. `sum()` returns `int | highs_linear_expression` and `addConstr` rejects it.
- Use `h.changeColBounds(col, lb, ub)` (single) or `h.changeColsBounds(...)` (batch) for edge fixations. Build the model once, mutate bounds across branches.
- A single `highspy.Highs()` model **cannot be safely re-used** across BnB child nodes without full state restoration. Use one `LPRelaxation` per node, plus a global `CutPool` shared by all nodes, plus basis warm-starting via `parent_basis` threaded from parent to child.

### TSP subtour elimination

- A subtour elimination cut is **violated** when the sum of crossing edges is strictly less than 2. Use `cut_value < 2 - tol` (with tolerance subtracted), **not** `< 2 + tol`.
- `nx.connected_components()` returns a generator of `set[int]`. To get `list[list[int]]`, wrap with `[sorted(c) for c in nx.connected_components(g)]`.

## `BranchingDecisions` API

Takes **edge indices (int)**, not `(u, v)` tuples. The mapping is the caller's responsibility — it must match the edge ordering used by `LPRelaxation`.

```python
from tsp_bnb.branching_decisions import BranchingDecisions, edge_index_of

decisions = BranchingDecisions(num_edges)
decisions.fix(edge_index_of(graph.edges, 0, 1), 1)  # NOT decisions.fix((0, 1), 1)
# No `fix_edge` method exists.
```

`fix(edge_index, value)` raises `ValueError` if value is not 0 or 1, or if the edge is already fixed.

## Frontend conventions

- **Spacing & sizing scale** (from _Refactoring UI_): in code we write ourselves, use only Tailwind spacing values `1 2 3 4 6 8 12 16 24 32 48 64 96 128 160 192` (px = value × 4). Never in-between values (`p-5`, `gap-14`, `w-[18px]`) in our own code — the scale is enforced by convention. shadcn components' internal values (`gap-1.5`, `h-8`, `size-3.5`) are exempt. Full table in ARCHITECTURE.md.
- TypeScript path alias `@/` → `src/` is configured in BOTH `frontend/tsconfig.app.json` (paths) and `frontend/vite.config.ts` (resolve.alias). Changing one without the other breaks either the type checker or the bundler.
- React Flow: `nodeTypes`/`edgeTypes` maps at **module scope**, never inline in a component.
- Theming: shadcn CSS-variable tokens in `index.css` (`:root`/`.dark`), toggled by `components/theme-provider.tsx`; React Flow gets `colorMode={resolvedTheme}`.
- Colors: UI chrome uses the existing shadcn tokens only; raw Tailwind ramps (`bg-emerald-600` …) for one-off decoration. Colors that carry meaning become tokens (`--bnb-status-*`, `--warning`) with a `.dark` twin (same H, +L, ×~0.6 C). Tokens are defined at anchor strength; all softer variants are opacity modifiers from the fixed set `10 20 30 50 80` (`/10`–`/20` tinted surface, `/50` ring, `/80` hover, `/30`–`/70` de-emphasis). Full rules in ARCHITECTURE.md "Color & opacity conventions".
- pre-commit: the root `prettier` hook excludes `frontend/`; the `prettier-frontend` hook runs frontend's own prettier via `scripts/prettier-frontend.sh` (requires `pnpm -C frontend install`).
- Never track Vite's `.vite/` dependency cache.

## Test conventions

- All test files must be `test_*.py` (enforced by pre-commit `name-tests-test --pytest-test-first`).
- Mark HiGHS-dependent or expensive tests with `@pytest.mark.slow` (marker defined in `pyproject.toml`).
- Shared fixtures in `tests/conftest.py`: `square_instance` (4-city, optimal=4.0), `triangle_instance` (3-city, LP is integral), `fresh_pool`, `empty_decisions`.
- Include a custom message in every `assert` — pre-commit / pytest output is much more useful.

## Project structure

- `tsp_bnb/` — algorithm package. The actual Python code (HiGHS, NetworkX, Pydantic).
- `tsp_bnb/export/` — Pydantic export models, matplotlib/networkx SVG renderer, `BnBSerializer` (writes `bnb_state.json` + run directory), `viewer.py` (detached localhost server + `runs/index.json` catalog).
- `examples/` — TSPLIB loader (`tsplib.py`, rejects non-`EUC_2D` instances) and `data/` with the TSPLIB archive.
- `frontend/` — React + Vite + pnpm visualizer (React Flow, shadcn/ui, Tailwind v4). See ARCHITECTURE.md for the `src/` layout.
- `tests/` — pytest tests + `conftest.py`.
- `main.py` — TSPLIB BnB runner: instance registry (`RUNS`, typed `Tier`) + CLI (`uv run main.py [instances] [--list|--limit N|--no-browser|--no-export]`; bare run = eil51 + st70).
- `ARCHITECTURE.md` / `PLAN.md` — system design and roadmap.

## Tooling

- Type check: **pyrefly** (not mypy). Config in `[tool.pyrefly]` of `pyproject.toml`.
- Lint + format: **ruff** (via pre-commit).
- Property tests: **hypothesis** + **pytest**.
- pre-commit hooks: pyrefly, ruff, prettier (+ `prettier-frontend`), blacken-docs, shellcheck, uv-lock, uv-export, name-tests-test, disallow-caps.

## Reference

- HiGHS Python API: <https://highspy.readthedocs.io/> — use the modelling API (`addVariable`, `addConstr`, `minimize`, `changeColBounds`, `vals()`) over the low-level matrix API for readability.
- Pydantic v2 for all data models. Use `model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)` when storing `nx.Graph` or other non-pydantic types.
- NetworkX 3.6+ typing: use `nx.Graph[int, NodeData, EdgeData]` for type hints, but wrap with `TYPE_CHECKING` for runtime (NetworkX 3.6.1 does not support runtime subscripting of `nx.Graph`).
