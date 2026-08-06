from collections.abc import Iterable


class CutPool:
    """
    Global pool of subtour elimination cuts shared across BnB nodes.

    A cut S is stored as its **canonical form** — the smaller of S and V\\S,
    tiebroken by sorted order — so the same logical cut is never stored twice.

    Cut insertion is monotonic: cuts are added but never removed. This
    keeps LPRelaxationSolver model structure (row order) stable across
    parent and child nodes, which is what makes basis warm-starting work
    later via setBasis().
    """

    def __init__(self, nodes: Iterable[int]):
        self._nodes = frozenset(nodes)
        self._cuts: set[frozenset[int]] = set()

    def __len__(self) -> int:
        return len(self._cuts)

    def __contains__(self, subtour: Iterable[int]) -> bool:
        return self._canonicalize(frozenset(subtour)) in self._cuts

    def __bool__(self) -> bool:
        return bool(self._cuts)

    def add(self, subtour: Iterable[int]) -> frozenset[int] | None:
        """
        Register a new cut. Duplicates and complements are silently ignored.
        Returns the canoncial form, or None if degenerate.
        """
        s = frozenset(subtour)
        canonical = self._canonicalize(s)
        if canonical is not None:
            self._cuts.add(canonical)
        return canonical

    def all(self) -> list[frozenset[int]]:
        """Return all cuts in deterministic order: shorter first, then lex."""
        return sorted(self._cuts, key=self._sort_key)

    def _canonicalize(
        self, subtour: set[int] | frozenset[int]
    ) -> frozenset[int] | None:
        """
        Return the canonical subtour (S or V\\S). The canonical set is either the smaller set or the lexicographically smaller one. Return None if degenerate (full or empty set)
        """
        if not subtour or subtour == self._nodes:
            return None
        complement = frozenset(self._nodes - subtour)
        # Prefer the shorter set
        if len(subtour) < len(complement):
            return frozenset(subtour)
        if len(complement) < len(subtour):
            return complement

        # Same length: tiebreak on sorted tuple
        return (
            frozenset(subtour)
            if self._sort_key(subtour) <= self._sort_key(complement)
            else complement
        )

    # --- internals ---

    @staticmethod
    def _sort_key(subtour: set[int] | frozenset[int]) -> tuple[int, tuple[int, ...]]:
        """Comparison key: shorter first, then lex-sorted tuple of node IDs."""
        return (len(subtour), tuple(sorted(subtour)))
