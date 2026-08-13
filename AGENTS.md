# AGENTS.md

Repository: TSP Branch-and-Bound visualizer (Python + HiGHS, Vue + D3 frontend).
Read `ARCHITECTURE.md` and `PLAN.md` for the high-level design before starting.

## Setup

Python 3.14+. All package management via `uv` (lockfile is `uv.lock`).

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

Frontend tooling uses Node 22 (`mise.toml`).

`pyproject.toml` configures `pythonpath = ["tsp_bnb"]` and `search-path = ["tsp_bnb"]` for pytest / pyrefly / pyright — so tests and source files can `from tsp_bnb import ...` directly without an editable install.

## Critical landmines

### `tsp_bnb/visualization.py` blocks every test import

`visualization.py` does `from jinja2 import Template` at module top, and `progress_tracker.py` imports it unconditionally. `jinja2` is not in `pyproject.toml` deps. As a result **every** test fails with `ModuleNotFoundError: No module named 'jinja2'` even when unrelated to visualization. The file is dead knapsack-era code that also references removed methods (`BnBNode.cost()`, `BranchingDecisions.included_items()`, `does_obey_capacity_constraint`).

Fix once, in order of effort:

- **A:** delete `tsp_bnb/visualization.py`, remove the import in `progress_tracker.py`, and remove any calls to it.
- **B:** lazy-import `BnBVisualization` inside the methods that use it; guard `_vis.X()` calls with `if self._vis: ...`.

Without one of these, no test can run.

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

## Test conventions

- All test files must be `test_*.py` (enforced by pre-commit `name-tests-test --pytest-test-first`).
- Mark HiGHS-dependent or expensive tests with `@pytest.mark.slow` (marker defined in `pyproject.toml`).
- Shared fixtures in `tests/conftest.py`: `square_instance` (4-city, optimal=4.0), `triangle_instance` (3-city, LP is integral), `fresh_pool`, `empty_decisions`.
- Include a custom message in every `assert` — pre-commit / pytest output is much more useful.

## Project structure

- `tsp_bnb/` — algorithm package. The actual Python code (HiGHS, NetworkX, Pydantic).
- `frontend/` — Vue + D3 visualizer (stub, not yet implemented).
- `server/` — FastAPI WebSocket server (stub, not yet implemented).
- `tests/` — pytest tests + `conftest.py`.
- `main.py` — placeholder entry point (`print("Hello from bnb-visualizer!")`).
- `ARCHITECTURE.md` — full system design.
- `PLAN.md` — implementation roadmap and current status.

The visualization (frontend) is the main development effort per supervisor direction.

## Tooling

- Type check: **pyrefly** (not mypy). Config in `[tool.pyrefly]` of `pyproject.toml`.
- Lint + format: **ruff** (via pre-commit).
- Property tests: **hypothesis** + **pytest**.
- pre-commit hooks: pyrefly, ruff, prettier, blacken-docs, shellcheck, uv-lock, uv-export, name-tests-test, disallow-caps.

## Reference

- Reuse BnB structure from `../alglab/ws2526_alglab_internal/sheets/02_bnb`.
- HiGHS Python API: <https://highspy.readthedocs.io/> — use the modelling API (`addVariable`, `addConstr`, `minimize`, `changeColBounds`, `vals()`) over the low-level matrix API for readability.
- Pydantic v2 for all data models. Use `model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)` when storing `nx.Graph` or other non-pydantic types.
- NetworkX 3.6+ typing: use `nx.Graph[int, NodeData, EdgeData]` for type hints, but wrap with `TYPE_CHECKING` for runtime (NetworkX 3.6.1 does not support runtime subscripting of `nx.Graph`).
