"""
Branch-and-bound is a tree-based search for the Traveling Salesman Problem.
At each node, it:
  1. Computes a lower bound via an LP relaxation to estimate the cheapest possible tour.
  2. Prunes subproblems whose bound cannot beat the current best feasible tour.
  3. Splits (branches) on edge variables to explore promising regions of the search space.
  4. Optionally applies heuristics to quickly find feasible tours and improve pruning.

This module provides the BnB solver with four interchangeable components:
  - Relaxation: compute lower bounds via the fractional TSP LP
  - OpenNodeContainer: manage the open node list (e.g., best-bound, BFS, DFS)
  - BranchingStrategy: decide which edge to branch on
  - Heuristics: generate feasible tours to improve pruning
"""

import logging
from pathlib import Path

from .bnb_nodes import BnBNode, NodeFactory, NodeStatus
from .branching_strategy import BranchingStrategy
from .cut_pool import CutPool
from .data_schema import TSPInstance, TSPSolution
from .export import BnBSerializer
from .heuristics import Heuristics
from .open_nodes import OpenNodeQueue
from .progress_tracker import ProgressTracker
from .relaxation import Relaxation, RelaxedSolution
from .solution_pool import SolutionPool

logger = logging.getLogger(__name__)


class TSPBnb:
    """
    Branch-and-bound solver for the Traveling Salesman Problem.

    Usage:
        searcher = BnBSearch(
            instance,
            relaxation=my_relaxation,
            search_strategy=my_search_strategy,
            branching_strategy=my_branching,
            root_heuristics=my_heuristics,
        )
        best = searcher.search(iteration_limit=10000)
    """

    def __init__(
        self,
        instance: TSPInstance,
        *,
        relaxation_cls: type[Relaxation],
        node_queue: OpenNodeQueue,
        branching_strategy: BranchingStrategy,
        root_heuristics: Heuristics,
        serializer: BnBSerializer | None = None,
    ):
        # Core attributes
        self.instance = instance
        self.relaxation = relaxation_cls
        self.node_queue = node_queue
        self.branching_strategy = branching_strategy
        self.root_heuristics = root_heuristics

        # Data structures for solutions and progress tracking
        self.solutions = SolutionPool()
        self.cut_pool = CutPool(instance.graph.nodes)
        self.serializer = serializer
        self.progress_tracker = ProgressTracker(
            instance, node_queue, self.solutions, serializer=serializer
        )

        # Factory to create tree nodes, with callback on new node
        self.node_factory = NodeFactory(
            instance=instance,
            relaxation_cls=relaxation_cls,
            on_new_node=self.progress_tracker.on_new_node_in_tree,
            cut_pool=self.cut_pool,
        )

    def _process_node(self, node: BnBNode) -> NodeStatus:
        """
        Process a single node:
          1. Prune if infeasible or bound too low.
          2. Accept if solution is feasible (integral and a single tour).
          3. Apply heuristics to discover additional feasible solutions.
          4. Branch otherwise.
        Returns the node status after processing.
        """
        sol: RelaxedSolution = node.relaxed_solution

        # 1. Infeasibility prune
        if sol.is_infeasible():
            node.status = NodeStatus.INFEASIBLE
            return NodeStatus.INFEASIBLE

        # 2. Bound-based prune: no better solution possible
        if sol.lower_bound >= self.solutions.best_solution_value():
            node.status = NodeStatus.PRUNED
            return NodeStatus.PRUNED

        # 3. Feasible solution found: integral
        if sol.is_integral():
            if sol.is_feasible_tour():
                feasible_sol = TSPSolution(
                    edge_selection=[
                        1 if val > 0.5 else 0 for val in sol.edge_fractions
                    ],
                    cost=sol.objective_value,
                )
                self.solutions.add(feasible_sol)
                self.progress_tracker.on_feasible_solution(feasible_sol)
                node.status = NodeStatus.INTEGER
                return NodeStatus.INTEGER
            # Integral but disjoint subtours — cut loop failed to eliminate them.
            # This node is a dead end: branching can't help (no fractional edges
            # to branch on), and the "solution" isn't a valid tour.
            node.status = NodeStatus.INFEASIBLE
            return NodeStatus.INFEASIBLE

        # TODO: is heuristic on every node needed?
        # # 4. Heuristic improvement: generate extra feasible solutions
        # for heur_sol in self.heuristics.search(self.instance, node.relaxed_solution):
        #     # heur_sol must be feasible; pool enforces validity
        #     self.solutions.add(heur_sol)
        #     self.progress_tracker.on_heuristic_solution(node, heur_sol)

        # 5. Branch on a fractional decision variable
        branches = self.branching_strategy.make_branching_decisions(node)
        if not branches:
            logger.warning(
                "No branches created for node %s; check branching strategy.", node
            )

        for decision in branches:
            child = self.node_factory.create_child(node, decision)
            self.node_queue.enqueue(child)

        node.status = NodeStatus.BRANCHED
        return NodeStatus.BRANCHED

    def search(self, iteration_limit: int = 10_000) -> TSPSolution | None:
        """
        Run the branch-and-bound algorithm to optimum or until iteration_limit is reached.

        Args:
            iteration_limit: max number of nodes to process before aborting.

        Returns:
            The best feasible solution found (relaxed) or None if none found.

        Raises:
            ValueError: if the iteration_limit is reached without completion.
        """

        # Initialize root node and progress tracking
        root = self.node_factory.create_root()
        self.node_queue.enqueue(root)
        self.progress_tracker.start_search()

        # Root heuristic for initial upper bound
        init_sol = self.root_heuristics.search(self.instance, relaxed=None)
        self.solutions.add(init_sol)
        self.progress_tracker.on_heuristic_solution(root, init_sol)
        # logger.info(f"Root heuristic: initial UB = {init_sol.cost:.3f}")

        for iteration in range(1, iteration_limit + 1):
            if not self.node_queue.has_next():
                break

            node = self.node_queue.next()
            self.progress_tracker.start_iteration(node)
            status = self._process_node(node)
            self.progress_tracker.end_iteration(status)

            # Global prune: no better solution exists
            if self.node_queue.lower_bound() >= self.solutions.best_solution_value():
                logger.info("Global prune at iteration %d", iteration)
                for pruned_node in self.node_queue.nodes_in_queue():
                    pruned_node.status = NodeStatus.PRUNED
                    self.progress_tracker.on_node_pruned(
                        pruned_node, self.solutions.best_solution()
                    )
                break

        else:
            # Iteration limit exhausted without finishing
            raise ValueError(f"Iteration limit of {iteration_limit} reached")

        self.progress_tracker.end_search()
        return self.solutions.best_solution()

    def save(self, *, open_browser: bool = True) -> Path:
        """Export the run: bnb_state.json + index.html + images.

        Requires TSPBnb(..., serializer=BnBSerializer(instance)) — the
        serializer collects tree events during search(), so it cannot be
        created retroactively here.

        Args:
            open_browser: ensure the viewer server, refresh the run catalog,
                and open this run in a browser tab after saving.

        Returns:
            The run directory containing the exported artifacts.
        """
        if self.serializer is None:
            raise RuntimeError(
                "No serializer attached: construct TSPBnb with "
                "serializer=BnBSerializer(instance) to enable export."
            )
        return self.serializer.save(open_browser=open_browser)
