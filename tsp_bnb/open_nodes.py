"""
Priority-based storage for open TSP branch-and-bound nodes.

You can implement your own priority functions, such as BFS, DFS and best_bound.
"""

import heapq
import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

from .bnb_nodes import BnBNode

type PriorityKey = tuple[float | int, ...]
type PriorityFunction = Callable[[BnBNode], PriorityKey]


# --- Priority functions ---
def best_bound_order(node: BnBNode) -> PriorityKey:
    """Prioritize nodes with the smallest relaxed lower bound."""
    return (node.relaxed_solution.lower_bound, node.depth)


def breadth_first_order(node: BnBNode) -> PriorityKey:
    """Prioritize nodes by increasing tree depth."""
    return (node.depth,)


def depth_first_order(node: BnBNode) -> PriorityKey:
    """Prioritize nodes by decreasing tree depth."""
    return (-node.depth,)


@dataclass(order=True, slots=True, frozen=True)
class _QueueEntry:
    """Heap entry containing priority, insertion order, and node."""

    priority: PriorityKey
    sequence: int
    node: BnBNode = field(compare=False)


class OpenNodeQueue:
    """Manage unexplored TSP nodes in a min-heap."""

    def __init__(self, priority: PriorityFunction = best_bound_order) -> None:
        """Create an open-node container using `priority` for heap ordering."""
        self._priority = priority
        self._queue: list[_QueueEntry] = []
        self._counter = 0

    def __len__(self) -> int:
        """Return number of open nodes."""
        return len(self._queue)

    def enqueue(self, node: BnBNode) -> None:
        """Add `node`; equal priorities retain insertion order."""
        entry = _QueueEntry(
            priority=self._priority(node), sequence=self._counter, node=node
        )
        heapq.heappush(self._queue, entry)
        self._counter += 1

    def has_next(self) -> bool:
        """Return whether any open node remains."""
        return bool(self._queue)

    def next(self) -> BnBNode:
        """Remove and return next node by priority.

        Raises:
            ValueError: if no open nodes remain.
        """
        if not self.has_next():
            raise ValueError("No more nodes to explore.")
        return heapq.heappop(self._queue).node

    def nodes_in_queue(self) -> Iterator[BnBNode]:
        """Iterate over a snapshot of open nodes without removing them."""
        return iter(entry.node for entry in self._queue)

    def lower_bound(self) -> float:
        """Return smallest open-node relaxed lower bound, or `math.inf` if empty."""
        return min(
            (node.relaxed_solution.lower_bound for node in self.nodes_in_queue()),
            default=math.inf,
        )
