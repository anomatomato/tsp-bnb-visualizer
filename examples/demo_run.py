"""Minimal, self-contained demo of the TSP branch-and-bound solver.

This file shows the whole workflow for a new user:

    1. build a TSP instance from a NetworkX graph,
    2. assemble a solver from its pluggable parts,
    3. run the search,
    4. export the run and open it in the browser visualizer.

Run it from the repository root:

    uv run python -m examples.demo_run

Both instances here are deliberately tiny, so the solver finishes at the root
node: the start heuristic already finds an optimal tour and the root LP bound
proves it. The tree in the viewer will therefore have a single node. To see
real branching, run a TSPLIB instance instead, e.g. ``uv run main.py eil51``.
"""

import logging

import networkx as nx

# The solver itself: owns the search loop, the open-node queue, the incumbent
# pool and the shared subtour-cut pool.
from tsp_bnb.bnb import TSPBnb

# Decides WHICH edge variable to branch on once a node's LP solution is
# fractional. Alternatives in the same module: FirstUndecidedBranchingStrategy,
# FirstFractionalBranchingStrategy.
from tsp_bnb.branching_strategy import (
    MostFractionalBranchingStrategy,
)

# Pydantic wrapper around an undirected, weighted nx.Graph.
from tsp_bnb.data_schema import TSPInstance

# Records every search event (node created, processed, pruned, new incumbent)
# and writes the run directory read by the frontend.
from tsp_bnb.export import BnBSerializer

# Start heuristics that give an initial upper bound (incumbent) before any LP
# is solved: nearest-neighbour construction, then improved with 2-opt.
from tsp_bnb.heuristics import NearestNeighborHeuristic, TwoOptImproved

# Decides in WHICH ORDER open nodes are processed. Alternatives in the same
# module: breadth_first_order, depth_first_order.
from tsp_bnb.open_nodes import OpenNodeQueue, best_bound_order

# The relaxation solved at every node: an LP (HiGHS) with degree constraints
# plus lazily added subtour-elimination cuts.
from tsp_bnb.relaxation import LPRelaxation

# Set up logging. INFO shows the solver's own messages (e.g. "Global prune at
# iteration N") and the export path. The per-iteration progress table is
# printed by the solver regardless of the logging level.
logging.basicConfig(
    level=logging.INFO,
    # format="%(asctime)s|%(levelname)s: %(message)s",
    # datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_square4(*, open_browser: bool = True):
    """4-city complete graph (square). Optimal tour cost = 8.

    Layout:
        0 -- 1
        |    |
        3 -- 2

    Edges: (0,1)=2, (0,2)=3, (0,3)=2, (1,2)=2, (1,3)=3, (2,3)=2
    Optimal: 0-1-2-3-0 = 2+2+2+2 = 8

    The square's sides are cheap (2) and its diagonals expensive (3), so the
    perimeter is the unique optimal tour.
    """
    # --- 1. Build the instance -------------------------------------------
    # The graph must be complete (every city connected to every other city)
    # and every edge needs a numeric "weight" attribute: the travel cost.
    # Node labels are plain ints.
    g = nx.Graph()
    g.add_edge(0, 1, weight=2)  # side
    g.add_edge(0, 2, weight=3)  # diagonal
    g.add_edge(0, 3, weight=2)  # side
    g.add_edge(1, 2, weight=2)  # side
    g.add_edge(1, 3, weight=3)  # diagonal
    g.add_edge(2, 3, weight=2)  # side

    # `name` is used for the run directory (output/runs/run_square4_<time>/)
    # and is shown in the viewer's run picker.
    instance = TSPInstance(graph=g, name="square4")

    # --- 2. Assemble the solver ----------------------------------------------
    # Every component can be swapped independently. These choices are the
    # project defaults.
    bnb = TSPBnb(
        instance=instance,
        # Pass the CLASS, not an instance: the solver creates one fresh LP per
        # tree node, warm-started from the parent's basis. All nodes share one
        # global pool of subtour cuts.
        relaxation_cls=LPRelaxation,
        # Best-bound search: always process the open node with the smallest
        # LP lower bound next (ties broken by depth). Raises the global lower
        # bound as fast as possible.
        node_queue=OpenNodeQueue(priority=best_bound_order),
        # Branch on the edge whose LP value is closest to 0.5, i.e. the edge
        # the LP is least sure about. Creates two children: edge forced out
        # (x_e = 0) and edge forced in (x_e = 1).
        branching_strategy=MostFractionalBranchingStrategy(),
        # Run once at the root to get a first feasible tour. A good incumbent
        # early lets the solver prune more nodes later. TwoOptImproved wraps
        # any construction heuristic and improves its tour with 2-opt moves.
        root_heuristics=TwoOptImproved(NearestNeighborHeuristic()),
        # Optional. Only needed if you want to export/visualize the run.
        # It must be attached BEFORE search(): it records events while the
        # search runs and cannot rebuild them afterwards. By default it does
        # not render backend SVG images (the frontend draws the tours itself).
        serializer=BnBSerializer(instance),
    )

    # --- 3. Run the search ---------------------------------------------------
    # Processes at most `iteration_limit` nodes (one node per iteration).
    # Returns the best tour found (a TSPSolution with .cost and
    # .edge_selection). If the limit runs out before optimality is proven,
    # search() raises IterationLimitReached (a ValueError subclass) instead.
    # The best tour so far is then still in bnb.solutions and the run can
    # still be exported (main.py does exactly that).
    solution = bnb.search(iteration_limit=100)
    logger.info(
        "Finished search with %d iterations.", bnb.progress_tracker.num_iterations
    )

    # Sanity checks for the demo: we know the optimum, so verify it.
    assert solution is not None, "BnB should return a solution"
    assert solution.cost == 8, f"Expected cost 8, got {solution.cost}"

    # --- 4. Export and visualize ---------------------------------------------
    # Writes output/runs/run_square4_<timestamp>/bnb_state.json (the complete,
    # replayable search tree) plus a fallback index.html.
    # With open_browser=True it also starts (or reuses) the local viewer
    # server on http://localhost:8123, adds the run to the run catalog and
    # opens it in a new browser tab. Pass open_browser=False to only write
    # files (e.g. in scripts or CI).
    run_dir = bnb.save(open_browser=open_browser)
    logger.info("%s: run exported to %s", instance.name, run_dir)


def run_pentagon5(*, open_browser: bool = True):
    """5-city complete graph with unit edge weights.

    All 10 edges of K5 cost 1, so EVERY tour costs exactly 5 and the LP
    bound at the root is also 5 (degree constraints: each city has two tour
    edges, so the total is 5 edges x 1). The start heuristic finds a tour of
    cost 5, the root LP proves no tour can be cheaper, and the root is pruned
    in the first iteration. The demo shows the full pipeline, not branching.
    """
    # K5 drawn as two overlaid 5-cycles. Together they cover all 10 edges:
    #   tour A = 0-1-2-3-4-0 (the pentagon's outline)
    #   tour B = 0-2-4-1-3-0 (the pentagram inside it)
    # With equal weights, A, B and every other tour tie at cost 5.
    # To experiment, change some weights (e.g. make tour A cheaper) and watch
    # how the result and the tree in the viewer change.
    g = nx.Graph()
    g.add_edge(0, 1, weight=1)  # A
    g.add_edge(1, 2, weight=1)  # A
    g.add_edge(2, 3, weight=1)  # A
    g.add_edge(3, 4, weight=1)  # A
    g.add_edge(4, 0, weight=1)  # A
    g.add_edge(0, 2, weight=1)  # B
    g.add_edge(2, 4, weight=1)  # B
    g.add_edge(4, 1, weight=1)  # B
    g.add_edge(1, 3, weight=1)  # B
    g.add_edge(3, 0, weight=1)  # B
    instance = TSPInstance(graph=g, name="pentagon5")

    # Same solver setup as in run_square4. See the comments there.
    bnb = TSPBnb(
        instance=instance,
        relaxation_cls=LPRelaxation,
        node_queue=OpenNodeQueue(priority=best_bound_order),
        branching_strategy=MostFractionalBranchingStrategy(),
        root_heuristics=TwoOptImproved(NearestNeighborHeuristic()),
        serializer=BnBSerializer(instance),
    )

    solution = bnb.search(iteration_limit=100)
    logger.info(
        "Finished search with %d iterations.", bnb.progress_tracker.num_iterations
    )

    assert solution is not None, "BnB should return a solution"
    logger.info("Best cost: %s", solution.cost)

    run_dir = bnb.save(open_browser=open_browser)
    logger.info("%s: run exported to %s", instance.name, run_dir)


if __name__ == "__main__":
    # Each call exports one run and opens its own browser tab. Both runs then
    # appear in the viewer's run picker, alongside every earlier run.
    run_pentagon5()
    run_square4()
