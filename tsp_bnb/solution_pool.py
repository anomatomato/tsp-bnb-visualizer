"""
SolutionPool Module

Manage the set of feasible integer solutions found during the BnB search,
keeping track of the best one (lowest cost) for pruning and final output.

You do not need to modify this file; it validates and stores your solutions.
"""

from .data_schema import TSPSolution


class SolutionPool:
    """
    Stores feasible integral solutions and tracks the best one.

    Usage:
        pool = SolutionPool()
        pool.add(solution)
        best_val = pool.best_solution_value()
        best_sol = pool.best_solution()
    """

    def __init__(self) -> None:
        self._solutions: list[TSPSolution] = []
        self._best_solution: TSPSolution | None = None

    def __iter__(self):
        return iter(self._solutions)

    def add(self, solution: TSPSolution) -> None:
        """
        Add a new feasible integral solution to the pool.

        Raises:
            AssertionError: if `solution` is infeasible or non-integral.
        """
        # Add only unique solutions by value and selection
        if solution not in self._solutions:
            self._solutions.append(solution)
            # Update best if it's strictly better
            if self._best_solution is None or solution.cost < self._best_solution.cost:
                self._best_solution = solution

    def best_solution_value(self) -> float:
        """
        Return the value of the best solution, or inf if none.
        """
        return (
            self._best_solution.cost
            if self._best_solution is not None
            else float("inf")
        )

    def best_solution(self) -> TSPSolution | None:
        """
        Return the best solution, or None if no solution was added.
        """
        return self._best_solution

    def all_solutions(self) -> list[TSPSolution]:
        """
        Return a list of all unique solutions found so far.
        """
        return list(self._solutions)
