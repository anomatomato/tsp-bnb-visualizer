"""
ProgressTracker Module

Track and display detailed statistics of your branch-and-bound search.
You will see iteration counts, node creation/exploration, depth, status, and bounds.

You can customize the printed table or integrate further visualization callbacks.
"""

from datetime import datetime

from .bnb_nodes import BnBNode, NodeStatus
from .data_schema import TSPInstance, TSPSolution
from .export import BnBSerializer
from .open_nodes import OpenNodeQueue
from .solution_pool import SolutionPool


class ProgressTracker:
    """
    Monitors and reports BnB search progress:
      - iteration count
      - nodes created vs. explored
      - current node depth and status
      - current node value, global UB and LB
      - visualization callbacks
    """

    def __init__(
        self,
        instance: TSPInstance,
        search_strategy: OpenNodeQueue,
        solutions: SolutionPool,
        serializer: BnBSerializer | None = None,
    ) -> None:
        """`serializer` is optional: pass None for search runs without export
        (tests, benchmarks) — no SVG rendering, no output directories."""
        self._instance = instance
        self._search = search_strategy
        self._solutions = solutions
        self._serializer = serializer

        self._start_time: datetime | None = None
        self.num_iterations = 0
        self._nodes_created = 0
        self._current_node: BnBNode | None = None

    def upper_bound(self) -> float:
        """Best feasible tour cost found so far (incumbent)."""
        return self._solutions.best_solution_value()

    def lower_bound(self) -> float:
        """Global lower bound = min LP bound over all open nodes."""
        return self._search.lower_bound()

    def on_new_node_in_tree(self, node: BnBNode) -> None:
        """Called whenever a new node is generated."""
        self._nodes_created += 1
        if self._serializer is not None:
            self._serializer.on_new_node_in_tree(node, iteration=self.num_iterations)

    def on_heuristic_solution(self, node: BnBNode, sol: TSPSolution) -> None:
        """Called when a heuristic finds a new feasible solution."""
        # if sol.value() >= self._solutions.best_solution_value():
        node.heuristic_solution = sol
        # print(
        #     f"[Heuristic] node {node.node_id} -> new feasible solution {sol} (cost={sol.cost:.3f})"
        # )

        if self._serializer is not None:
            self._serializer.on_heuristic_solution(node, sol)

        self.on_feasible_solution(sol)

    def on_feasible_solution(self, sol: TSPSolution) -> None:
        """Called when a feasible solution is found (integral LP or heuristic)."""
        if self._serializer is not None and sol == self._solutions.best_solution():
            self._serializer.on_best_solution_updated(
                sol, iteration=self.num_iterations
            )

    def on_node_global_pruned(
        self, node: BnBNode, best_solution: TSPSolution | None, global_lb: float
    ) -> None:
        """Called whenever a node is globally pruned."""
        if self._serializer is not None:
            self._serializer.on_node_global_pruned(
                node,
                iteration=self.num_iterations,
                incumbent=best_solution.cost if best_solution else None,
                lb=global_lb,
            )

    def start_search(self) -> None:
        """Initialize search reporting and print header."""
        self._start_time = datetime.now().astimezone()
        header = (
            f"{'Iter':>5} {'Explored/Total':>15} {'Depth':>5} "
            f"{'Status':>10} {'NodeLB':>12} {'Incumbent':>11} {'GlobalLB':>11}"
        )
        print(f"BnB search started for '{self._instance.name}':")
        print(header)
        print("=" * len(header))

    def start_iteration(self, node: BnBNode) -> None:
        """Begin processing a node."""
        self.num_iterations += 1
        self._current_node = node

    def end_iteration(self, status: NodeStatus) -> None:
        """Finish processing a node and report its stats."""
        if self._current_node is None:
            return
        explored = self.num_iterations
        total = self._nodes_created
        depth = self._current_node.depth
        node_lb = self._current_node.relaxed_solution.lower_bound
        incumbent = self.upper_bound()
        global_lb = self.lower_bound()
        print(
            f"{self.num_iterations:5d} {explored:7d}/{total:<6d}{depth:5d} "
            f"{status.value:>13} {node_lb:10.1f} {incumbent:10.1f} {global_lb:11.1f}"
        )
        # Visualization callback
        if self._serializer is not None:
            self._serializer.on_node_processed(
                self._current_node,
                lb=global_lb,
                ub=incumbent,
                iteration=self.num_iterations,
            )
        # reset per-iteration data
        self._current_node = None

    def end_search(self) -> None:
        """Finalize reporting and output summary and visualization."""
        duration = (
            datetime.now().astimezone() - self._start_time if self._start_time else None
        )
        print("\nSearch finished.")
        print(
            f"Iterations: {self.num_iterations}, Nodes created: {self._nodes_created}."
        )
        # best = self._solutions.best_solution()
        val = self._solutions.best_solution_value()
        print(f"Best solution: cost {val:.3f}.")
        if duration:
            print(f"Elapsed time: {duration}.")
        # write visualization
        # ts = datetime.now().astimezone().strftime("%Y-%m-%d_%Hh-%Mm-%Ss")
        # self._vis.visualize(
        #     self._solutions.best_solution(), f"bnb-{self._instance.name}_{ts}.html"
        # )
