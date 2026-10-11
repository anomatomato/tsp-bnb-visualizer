"""BnBSerializer: collects BnB state during search, writes JSON + SVGs at end."""

import logging
import webbrowser
from datetime import datetime
from pathlib import Path

from ..bnb_nodes import BnBNode, InfeasibleReason, NodeStatus, PruneReason
from ..data_schema import TSPInstance, TSPSolution
from .models import (
    BestSolutionEntry,
    BnBRunData,
    EdgeData,
    InstanceData,
    NodePosition,
    NodeVisData,
    RelaxedSnapshot,
    SolverConfigData,
    TourSnapshot,
)
from .renderer import compute_kamada_kawai_positions, render_lp_solution, render_tour

logger = logging.getLogger(__name__)


class BnBSerializer:
    """Collects BnB state during search, renders SVGs, writes JSON at end.

    Integration: ProgressTracker owns a BnBSerializer instance and forwards
    events to it. TSPBnb never calls BnBSerializer directly.
    """

    def __init__(
        self, instance: TSPInstance, output_root: Path = Path("output")
    ) -> None:
        self._instance: TSPInstance = instance
        self._output_root: Path = output_root
        self.positions = compute_kamada_kawai_positions(instance)

        # State collected during search
        self._root: NodeVisData | None = None
        self._node_data: dict[int, NodeVisData] = {}
        self._best_solutions: list[BestSolutionEntry] = []
        self._processing_order: list[int] = []

        # Run directory paths (computed upfront, created lazily on first render).
        # Computing paths here keeps the types as Path (not Path | None), so
        # render calls stay clean — no Optional unwrapping needed. One clock
        # read, two spellings: `started_at` goes into BnBRunData (the JSON is
        # self-describing), `ts` into the filesystem-safe run dir name — the
        # two can never drift apart.
        now = datetime.now().astimezone()
        self._started_at = now.isoformat(timespec="seconds")
        ts = now.strftime("%Y-%m-%dT%H-%M-%S")
        self._run_dir: Path = self._output_root / "runs" / f"run_{instance.name}_{ts}"
        self._images_dir: Path = self._run_dir / "images"
        self._dirs_created: bool = False

    # --- Callbacks (called by ProgressTracker) ---

    def on_new_node_in_tree(self, node: BnBNode, *, iteration: int) -> None:
        """Called when a new node is created. Add to tree structure."""
        data = NodeVisData(
            node_id=node.node_id,
            parent_id=node.parent_id,
            depth=node.depth,
            created_at=iteration,
            status=node.status,
            lb=None,
            ub=None,
            processed_at=None,
            relaxed_solution=None,
            heuristic_solution=None,
            fixed_edges=None,
            pruned_at=None,
            prune_reason=None,
            infeasible_reason=None,
            branched_edge=None,
            children=[],
        )
        if node.parent_id is None:
            self._root = data
        else:
            self._node_data[node.parent_id].children.append(data)
        self._node_data[node.node_id] = data

    def on_node_processed(
        self, node: BnBNode, *, lb: float, ub: float, iteration: int
    ) -> None:
        """Called when a node is processed. Record bounds, render LP SVG."""
        self._processing_order.append(node.node_id)

        data = self._node_data[node.node_id]
        data.processed_at = iteration
        data.lb = lb
        data.ub = ub
        data.status = node.status
        # Per-edge fixation state for frontend tooltips
        data.fixed_edges = list(node.branching_decisions)

        match node.status:
            case NodeStatus.PRUNED:
                data.pruned_at = iteration  # == processed_at; harmless duplication
                data.prune_reason = PruneReason.NODE_BOUND
            case NodeStatus.INFEASIBLE:
                data.infeasible_reason = (
                    InfeasibleReason.LP_INFEASIBLE
                    if node.relaxed_solution.is_infeasible()
                    else InfeasibleReason.SUBTOURS
                )
            case NodeStatus.BRANCHED:
                data.branched_edge = node.branched_edge
            case _:
                pass

        self._record_relaxed_snapshot(data, node)

    def _record_relaxed_snapshot(self, data: NodeVisData, node: BnBNode) -> None:
        """Store the node's LP relaxation snapshot (and render its SVG).

        Shared by processed and pruned nodes: the creation-time LP is a real
        bound for queue leftovers too (it ordered the best-bound heap), so the
        snapshot is honest data for both. Infeasible relaxations get no
        snapshot — there are no fractions worth showing.
        """
        if node.relaxed_solution.is_infeasible():
            return
        filename = f"relaxation_{node.node_id}.svg"
        self._ensure_dirs()
        render_lp_solution(
            self._instance,
            self.positions,
            list(node.relaxed_solution.edge_fractions),
            self._images_dir / filename,
        )
        data.relaxed_solution = RelaxedSnapshot(
            edge_fractions=node.relaxed_solution.edge_fractions,
            objective=node.relaxed_solution.objective_value,
            is_integral_tour=node.relaxed_solution.is_feasible_tour(),
            image_path=f"images/{filename}",
        )

    def on_node_global_pruned(
        self,
        node: BnBNode,
        *,
        iteration: int,
        incumbent: float | None = None,
    ) -> None:
        """Called when a queue-leftover node is pruned (global prune at end).

        These nodes were never processed: no processing_order entry and no
        processed_at. The incumbent at the global-prune decision is exported
        as `ub`, and `pruned_at` records the prune iteration. Their
        creation-time LP is still real data — record fixed edges and the
        relaxed snapshot so the inspector can show what the search skipped.
        """
        data = self._node_data[node.node_id]
        data.status = node.status  # NodeStatus.PRUNED
        data.fixed_edges = list(node.branching_decisions)
        data.ub = incumbent
        data.pruned_at = iteration
        data.prune_reason = PruneReason.GLOBAL_BOUND
        self._record_relaxed_snapshot(data, node)

    def on_heuristic_solution(
        self,
        node: BnBNode,
        solution: TSPSolution,
    ) -> None:
        """Called when a heuristic finds a feasible tour. Render tour SVG."""
        filename = f"heuristic_{node.node_id}.svg"
        self._ensure_dirs()
        render_tour(
            self._instance,
            self.positions,
            list(solution.edge_selection),
            self._images_dir / filename,
        )

        data = self._node_data[node.node_id]
        data.heuristic_solution = TourSnapshot(
            edge_selection=solution.edge_selection,
            cost=solution.cost,
            image_path=f"images/{filename}",
        )

    def on_best_solution_updated(
        self, solution: TSPSolution, *, iteration: int
    ) -> None:
        """Called when the incumbent improves. Add to best_solutions timeline."""
        filename = f"best_{iteration}.svg"
        self._ensure_dirs()
        render_tour(
            self._instance,
            self.positions,
            list(solution.edge_selection),
            self._images_dir / filename,
        )

        entry = BestSolutionEntry(
            iteration=iteration,
            cost=solution.cost,
            edge_selection=solution.edge_selection,
            image_path=f"images/{filename}",
        )
        self._best_solutions.append(entry)

    # --- Helpers ---

    def _ensure_dirs(self) -> None:
        """Create run + images directories on first render. Idempotent."""
        if self._dirs_created:
            return
        self._images_dir.mkdir(parents=True, exist_ok=True)
        self._dirs_created = True

    def _instance_data(self) -> InstanceData:
        """Build InstanceData from instance + cached positions."""
        nodes = [NodePosition(id=i, x=x, y=y) for i, (x, y) in self.positions.items()]
        edges = [
            EdgeData(u=u, v=v, weight=weight)
            for u, v, weight in self._instance.graph.edges.data("weight")
        ]
        return InstanceData(name=self._instance.name, nodes=nodes, edges=edges)

    def _write_index_html(self, run_dir: Path, run_data: BnBRunData) -> None:
        """Write minimal index.html with links to JSON + images."""
        best_cost = (
            run_data.best_solutions[-1].cost if run_data.best_solutions else "N/A"
        )
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BnB Run — {run_data.instance.name}</title>
        </head>
        <body>
            <h1>BnB Run — {run_data.instance.name}</h1>
            <p>Nodes in tree: {len(run_data.processing_order)}</p>
            <p>Best solutions found: {len(run_data.best_solutions)}</p>
            <p>Best cost: {best_cost}</p>
            <ul>
                <li><a href="bnb_state.json">View bnb_state.json</a></li>
                <li><a href="images/">View images directory</a></li>
            </ul>
            <p><em>Frontend not yet built. This is a placeholder index page.</em></p>
        </body>
        </html>
        """
        (run_dir / "index.html").write_text(html, encoding="utf-8")

    # --- Final save ---

    def save(
        self, *, open_browser: bool = True, solver_config: SolverConfigData
    ) -> Path:
        """Write bnb_state.json + index.html, optionally open the viewer. Return run dir."""
        if self._root is None:
            raise ValueError("No nodes to serialize.")

        run_data = BnBRunData(
            instance=self._instance_data(),
            tree=self._root,
            best_solutions=self._best_solutions,
            processing_order=self._processing_order,
            started_at=self._started_at,
            solver_config=solver_config,
        )
        # A run with no rendered SVG (e.g. an infeasible root) never created dirs.
        self._run_dir.mkdir(parents=True, exist_ok=True)
        json_path = self._run_dir / "bnb_state.json"
        json_path.write_text(run_data.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"BnB state saved to {json_path}")

        self._write_index_html(self._run_dir, run_data)

        if open_browser:
            self._open_in_viewer()

        return self._run_dir

    def _open_in_viewer(self) -> None:
        """Best-effort viewer delivery: ensure server, refresh catalog, open tab.

        The ordering is the invariant the viewer depends on: by the time the
        tab loads `?run=<id>`, `<id>` is already in the catalog. Failures must
        not crash save() — the artifacts are already on disk at this point.
        """
        try:
            # Deferred import: a top-level one would make the package __init__
            # chain import this module while `python -m tsp_bnb.export.viewer`
            # is executing it — runpy then double-imports and warns.
            from .viewer import ensure_viewer, write_run_index

            base = ensure_viewer()
            if base is None:
                # No published viewer: open the run-local stub page instead.
                if not webbrowser.open_new_tab(str(self._run_dir / "index.html")):
                    logger.warning("Browser refused to open the stub page.")
                return
            write_run_index()
            url = f"{base}/?run={self._run_dir.name}"
            if not webbrowser.open_new_tab(url):
                logger.warning("Browser refused to open %s.", url)
        except (OSError, webbrowser.Error) as e:
            logger.warning("Viewer plumbing failed (run is saved): %s", e)
