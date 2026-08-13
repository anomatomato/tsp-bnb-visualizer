import logging

from _tsplib import TspLibGraphInstanceDb
from tsp_bnb.bnb import TSPBnb
from tsp_bnb.branching_strategy import (
    MostFractionalBranchingStrategy,
)
from tsp_bnb.data_schema import TSPInstance
from tsp_bnb.heuristics import NearestNeighborHeuristic, TwoOptImproved
from tsp_bnb.open_nodes import OpenNodeContainer, best_bound_order
from tsp_bnb.relaxation import LPRelaxation

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    # format="%(asctime)s|%(levelname)s: %(message)s",
    # datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_att48():
    db = TspLibGraphInstanceDb()
    graph = db["att48"]
    instance = TSPInstance(graph=graph, name="att48")

    bnb = TSPBnb(
        instance=instance,
        relaxation_cls=LPRelaxation,
        search_strategy=OpenNodeContainer(priority=best_bound_order),
        branching_strategy=MostFractionalBranchingStrategy(),
        heuristics=TwoOptImproved(NearestNeighborHeuristic()),
    )

    solution = bnb.search(iteration_limit=10_000)
    logger.info(
        "Finished search with %d iterations.", bnb.progress_tracker.num_iterations
    )

    assert solution is not None, "BnB should return a solution"

    optimal_cost = 10_628
    assert solution.cost == optimal_cost, (
        "BnB should return the optimal solution for att48"
    )
    # assert bnb.progress_tracker.upper_bound() == 5, "The objective value should be 5."
    # assert bnb.progress_tracker.lower_bound() == 5, "The bound should be 5."


def main():
    run_att48()


if __name__ == "__main__":
    main()
