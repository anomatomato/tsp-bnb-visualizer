import logging

import networkx as nx
from tsp_bnb.bnb import TSPBnb
from tsp_bnb.branching_strategy import (
    MostFractionalBranchingStrategy,
)
from tsp_bnb.data_schema import TSPInstance
from tsp_bnb.export import BnBSerializer
from tsp_bnb.heuristics import NearestNeighborHeuristic, TwoOptImproved
from tsp_bnb.open_nodes import OpenNodeQueue, best_bound_order
from tsp_bnb.relaxation import LPRelaxation

# Set up logging
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
    """
    g = nx.Graph()
    g.add_edge(0, 1, weight=2)
    g.add_edge(0, 2, weight=3)
    g.add_edge(0, 3, weight=2)
    g.add_edge(1, 2, weight=2)
    g.add_edge(1, 3, weight=3)
    g.add_edge(2, 3, weight=2)
    instance = TSPInstance(graph=g, name="square4")

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
    assert solution.cost == 8, f"Expected cost 8, got {solution.cost}"

    run_dir = bnb.save(open_browser=open_browser)
    logger.info("%s: run exported to %s", instance.name, run_dir)


def run_pentagon5(*, open_browser: bool = True):
    """5-city graph that produces a fractional LP relaxation.

    Uses the classic fractional TSP example: a 5-node graph where the LP
    optimum is a convex combination of two tours, giving x_ij = 0.5 on
    some edges.
    """
    g = nx.Graph()
    # Two 5-cycles overlaid: tour A = 0-1-2-3-4-0, tour B = 0-2-4-1-3-0
    # Make tour A edges cheap, tour B edges cheap, cross edges expensive.
    # LP averages A and B → fractional on shared edges.
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
    run_pentagon5()
    run_square4()
