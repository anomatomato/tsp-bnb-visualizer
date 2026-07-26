class BranchingDecisions:
    """
    Per-node 0/1 branching decisions for a TSP BnB.

    Each edge of the TSP instance is in one of three states:
      - None:  free (may or may not be in the optimal tour)
      - 0:     forced OUT of the tour  (x_ij = 0)
      - 1:     forced INTO the tour   (x_ij = 1)

    The mapping (u, v) -> edge_index is the caller's responsibility and
    must match the edge ordering used by the LP relaxation.

    Args:
        num_edges (int): Number of edges (== number of LP variables).

    Methods:
        __getitem__(edge_index) -> int | None
            Get the fixation at edge_index (0, 1, or None).
        __len__() -> int
            Number of edges. Constant.
        __iter__() -> Iterator[int | None]
            Iterate over all fixations.
        fix(edge_index, value) -> None
            Force edge_index to 0 (out) or 1 (in).
        copy() -> BranchingDecisions
            Deep copy of the fixations.
        fixed_in_edges() -> list[int]
            Edge indices forced into the tour (x_ij = 1).
        fixed_out_edges() -> list[int]
            Edge indices forced out of the tour (x_ij = 0).
        is_fixed() -> bool
            True if every edge has a fixation (i.e. this is a leaf node).
        split_on(edge_index) -> (BranchingDecisions, BranchingDecisions)
            Return (force_out, force_in) children branching on edge_index.
    """

    def __init__(self, num_edges: int) -> None:
        """Initialize a fresh set of fixations (all unfixed)."""
        self._fixations: list[int | None] = [None] * num_edges

    def __getitem__(self, edge_index: int) -> int | None:
        """Return the fixation at edge_index (0, 1, or None)."""
        return self._fixations[edge_index]

    def __len__(self) -> int:
        return len(self._fixations)

    def __iter__(self):
        return iter(self._fixations)

    def __repr__(self) -> str:
        """Compact debugging view, e.g. BranchingDecisions(5: [_,0,1,_,1])."""
        body = ",".join("_" if v is None else str(v) for v in self._fixations)
        return f"BranchingDecisions({len(self)}: [{body}])"

    def copy(self) -> "BranchingDecisions":
        """Return a deep copy of these fixations."""
        new = BranchingDecisions(len(self))
        new._fixations = self._fixations.copy()
        return new

    def fixed_included_edges(self) -> list[int]:
        """Edge indices forced INTO the tour (x_ij = 1)."""
        return [i for i, v in enumerate(self._fixations) if v == 1]

    def fixed_excluded_edges(self) -> list[int]:
        """Edge indices forced OUT of the tour (x_ij = 0)."""
        return [i for i, v in enumerate(self._fixations) if v == 0]

    def is_fixed(self) -> bool:
        """True if every edge has a fixation (this is a leaf node)."""
        return all(v is not None for v in self._fixations)

    # --- Write ---
    def fix(self, edge_index: int, value: int) -> None:
        """
        Force edge_index to 0 (out of tour) or 1 (into tour).

        Only call if the fixation does not forbid the optimal solution.
        Raises ValueError if value is not 0/1 or the edge is already fixed.
        """
        if value not in {0, 1}:
            raise ValueError(f"value must be 0 or 1, got {value}")
        if self._fixations[edge_index] is not None:
            raise ValueError(f"edge {edge_index} is already fixed")
        self._fixations[edge_index] = value

    def split_on(
        self, edge_index: int
    ) -> tuple["BranchingDecisions", "BranchingDecisions"]:
        """
        Branch on edge_index.

        Returns two children:
          - left:  same fixations plus edge_index forced to 0 (out)
          - right: same fixations plus edge_index forced to 1 (in)

        Raises ValueError if edge_index is already fixed.
        """
        left = self.copy()
        right = self.copy()
        left.fix(edge_index, 0)
        right.fix(edge_index, 1)
        return left, right
