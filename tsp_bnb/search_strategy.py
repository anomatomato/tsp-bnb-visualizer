"""
Search Strategy Module

The search strategy determines which node you explore next in the BnB tree to
improve your lower or upper bound as quickly as possible. Provide a `priority`
function that ranks open nodes; this class manages a priority queue accordingly.

You can implement breadth-first, depth-first, best-first, or any custom order
by supplying different priority functions.
"""

import queue
from collections.abc import Callable, Iterator
from typing import Any

from .bnb_nodes import BnBNode


class SearchStrategy:
    """
    Manage open BnB nodes in a priority queue.

    Args:
        priority: callable mapping a BnBNode to a comparable key.
        Lower keys are explored first.
    """

    def __init__(self, priority: Callable[[BnBNode], Any]) -> None:
        self._priority = priority
        # use a counter to break ties by insertion order
        self._queue: queue.PriorityQueue[tuple[Any, int, BnBNode]] = (
            queue.PriorityQueue()
        )
        self._counter = 0

    def enqueue(self, node: BnBNode) -> None:
        """
        Add `node` to the open-set with its priority key.
        Ties are broken by the order nodes were added.
        """
        self._queue.put((self._priority(node), self._counter, node))
        self._counter += 1

    def has_next(self) -> bool:
        """
        Return True if there are still nodes to explore.
        """
        return not self._queue.empty()

    def next(self) -> BnBNode:
        """
        Remove and return the next node by priority.

        Raises:
            ValueError: if no nodes remain.
        """
        if not self.has_next():
            raise ValueError("No more nodes to explore.")
        return self._queue.get()[2]

    def __len__(self) -> int:
        """
        Number of nodes currently in the queue.
        """
        return self._queue.qsize()

    def nodes_in_queue(self) -> Iterator[BnBNode]:
        """
        Iterator over nodes still in the queue (no removal).
        """
        return (item[2] for item in self._queue.queue)

    def upper_bound(self) -> float:
        """
        Return the highest upper_bound among queued nodes, or -inf if empty.

        Note: to get the global BnB upper bound, take the max of this
        and your best feasible solution value.
        """
        if not self.has_next():
            return float("-inf")
        return max(
            self.nodes_in_queue(),
            key=lambda n: n.relaxed_solution.upper_bound,
        ).relaxed_solution.upper_bound


# Default search order: you must supply your own `priority`.
# This stub returns a constant key.


def my_search_order(node: BnBNode) -> Any:
    """
    Example default: constant priority.
    """
    return 0


# <Solution>


def best_first_search_order(node: BnBNode) -> tuple[float, int]:
    """
    Choose nodes with highest upper bound first; tie-break by smaller depth.
    """
    # negative because lower key is dequeued first
    return -node.relaxed_solution.upper_bound, node.depth


my_search_order = best_first_search_order  # type: ignore[assignment]  # noqa: F811
# </Solution>
