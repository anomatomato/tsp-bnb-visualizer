"""TSPLIB BnB runner: solve instances, export runs, open the viewer.

Usage:
    uv run main.py                       # default: eil51, then st70
    uv run main.py berlin52 kroA100      # explicit instances
    uv run main.py pcb442 --limit 300    # stress probe -> partial run exported
    uv run main.py kroA200 --no-export   # serializer-less timing, no artifacts
    uv run main.py --list
"""

import argparse
import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from examples.tsplib import TspLibGraphInstanceDb
from tsp_bnb.bnb import IterationLimitReached, TSPBnb
from tsp_bnb.branching_strategy import MostFractionalBranchingStrategy
from tsp_bnb.data_schema import TSPInstance
from tsp_bnb.export import BnBSerializer
from tsp_bnb.heuristics import NearestNeighborHeuristic, TwoOptImproved
from tsp_bnb.open_nodes import OpenNodeQueue, best_bound_order
from tsp_bnb.relaxation import LPRelaxation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_RUNS = ("eil51", "st70", "rat99")


class Tier(StrEnum):
    """Fixed run tiers — `--list` groups by these, in declaration order."""

    WARM_UP = "warm-up"
    MEDIUM = "medium"
    BIG = "big"


@dataclass(frozen=True)
class RunSpec:
    """Per-instance run parameters. Optima: TSPLIB95 certified values."""

    optimal: int
    tier: Tier
    iteration_limit: int = 10_000


RUNS: dict[str, RunSpec] = {
    # --- warm-up ---
    "eil51": RunSpec(426, Tier.WARM_UP),
    "st70": RunSpec(675, Tier.WARM_UP),
    "berlin52": RunSpec(7542, Tier.WARM_UP),
    "rat99": RunSpec(1211, Tier.WARM_UP),
    "kroA100": RunSpec(21282, Tier.WARM_UP),
    "eil101": RunSpec(629, Tier.WARM_UP),
    # --- medium ---
    "bier127": RunSpec(118282, Tier.MEDIUM),
    "ch150": RunSpec(6528, Tier.MEDIUM),
    "kroA200": RunSpec(29368, Tier.MEDIUM),
    "ts225": RunSpec(126643, Tier.MEDIUM),
    "a280": RunSpec(2579, Tier.MEDIUM),
    "lin318": RunSpec(42029, Tier.MEDIUM),
    # --- big: conservative probe limits so a bare name can't run for hours ---
    "pcb442": RunSpec(50778, Tier.BIG, iteration_limit=2_000),
    "pr439": RunSpec(107217, Tier.BIG, iteration_limit=2_000),
    "rat575": RunSpec(6773, Tier.BIG, iteration_limit=2_000),
}


def run_instance(
    db: TspLibGraphInstanceDb,
    name: str,
    spec: RunSpec,
    *,
    iteration_limit: int,
    open_browser: bool = True,
    export: bool = True,
) -> Path | None:
    """Solve one instance; export unless `export=False`. Return the run dir."""
    instance = TSPInstance(graph=db[name], name=name)
    # The serializer records events during search(), so it must exist first.
    serializer = BnBSerializer(instance) if export else None

    bnb = TSPBnb(
        instance=instance,
        relaxation_cls=LPRelaxation,
        node_queue=OpenNodeQueue(priority=best_bound_order),
        branching_strategy=MostFractionalBranchingStrategy(),
        root_heuristics=TwoOptImproved(NearestNeighborHeuristic()),
        serializer=serializer,
    )

    try:
        solution = bnb.search(iteration_limit=iteration_limit)
        completed = True
    except IterationLimitReached as e:
        # The incumbent survives in the pool and the serializer holds every
        # event so far, so the partial run is still exportable: undecided
        # nodes stay open and no global prune is recorded.
        logger.warning("%s: %s", name, e)
        solution = bnb.solutions.best_solution()
        completed = False

    if solution is None:
        logger.error("%s: no feasible solution found", name)
        return None

    gap = (solution.cost - spec.optimal) / spec.optimal
    if completed and abs(solution.cost - spec.optimal) < 1e-6:
        logger.info("%s: optimum %d confirmed", name, spec.optimal)
    elif completed:
        # Log-only by design: a long run should never die on a number, but a
        # finished search that misses the certified optimum is a real bug.
        logger.error(
            "%s: finished at %s but certified optimum is %d (gap %.2f%%)",
            name,
            solution.cost,
            spec.optimal,
            gap * 100,
        )
    else:
        logger.info(
            "%s: stopped at limit %d with incumbent %s (gap %.2f%% vs optimum %d)",
            name,
            iteration_limit,
            solution.cost,
            gap * 100,
            spec.optimal,
        )

    if not export:
        logger.info("%s: timing-only run, nothing exported", name)
        return None
    run_dir = bnb.save(open_browser=open_browser)
    logger.info("%s: run exported to %s", name, run_dir)
    return run_dir


def _positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be >= 1, got {value}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Solve TSPLIB instances with the TSP BnB solver."
    )
    parser.add_argument(
        "names",
        nargs="*",
        help=f"instances to run (default: {' '.join(DEFAULT_RUNS)})",
    )
    parser.add_argument(
        "--list", action="store_true", help="print the registry and exit"
    )
    parser.add_argument(
        "--limit",
        type=_positive_int,
        metavar="N",
        help="override every instance's iteration limit",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="export without opening a viewer tab",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="serializer-less timing run (no artifacts)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.list:
        for tier in Tier:  # declaration order = tier order
            print(f"[{tier}]")
            for name, spec in RUNS.items():
                if spec.tier is tier:
                    print(
                        f"  {name:<10} optimum {spec.optimal:<8} "
                        f"limit {spec.iteration_limit}"
                    )
        return

    names = args.names or list(DEFAULT_RUNS)
    unknown = [n for n in names if n not in RUNS]
    if unknown:
        raise SystemExit(f"unknown instance(s) {unknown}; valid: {sorted(RUNS)}")

    db = TspLibGraphInstanceDb()
    for name in names:
        spec = RUNS[name]
        run_instance(
            db,
            name,
            spec,
            iteration_limit=args.limit or spec.iteration_limit,
            open_browser=not args.no_browser,
            export=not args.no_export,
        )


if __name__ == "__main__":
    main()
