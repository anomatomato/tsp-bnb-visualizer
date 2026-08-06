from hypothesis import given, settings
from hypothesis import strategies as st
from tsp_bnb import CutPool

# --- Strategies ---
#
# `nodes_st` is a static strategy: a frozenset of distinct ints in [0, 15].
#
# `nodes_and_subtour` is a single `@st.composite` that draws a `nodes` set
# and then a non-empty proper subset `s` of it, returning them as a tuple.
# This is the idiomatic pattern per the Hypothesis docs:
# "We find that the greater readability of @composite usually outweighs
#  the verbosity" — `flatmap` is "old syntax for a special case of
#  @composite". One composite keeps the fixture shape in one place.

nodes_st = st.frozensets(
    st.integers(min_value=0, max_value=15), min_size=2, max_size=15
)


@st.composite
def nodes_and_subtour(draw) -> tuple[frozenset[int], frozenset[int]]:
    nodes = draw(nodes_st)
    sorted_nodes = sorted(nodes)
    s = draw(
        st.frozensets(
            st.sampled_from(sorted_nodes),
            min_size=1,
            max_size=max(0, len(nodes) - 1),
        )
    )
    return nodes, s


# --- Sanity tests ---


def test_empty_pool_is_false():
    """A newly created pool with no cuts chould be falsy."""
    assert not CutPool({0, 1, 2}), "A new CutPool with no cuts should be falsy"


def test_add_returns_canonical_form():
    """add() should return the canonical (smaller-side) form of the cut."""
    # Arrange
    pool = CutPool(nodes={0, 1, 2, 3, 4})
    # Act
    actual = pool.add([2, 3, 4])
    expected = frozenset({0, 1})
    # Assert
    assert actual == expected, (
        f"add([2,3,4]) should return canonical {{0,1}}, got {actual}"
    )


def test_add_and_complement_collapse_to_one():
    """A cut and its complement should be stored as a single entry."""
    pool = CutPool(nodes={0, 1, 2, 3, 4})
    pool.add([0, 1])
    pool.add([2, 3, 4])
    assert len(pool) == 1, (
        f"Complement cuts should collapse to 1 entry, got pool size {len(pool)}"
    )


def test_invalid_cuts_rejected():
    """Empty and full cuts should be rejected (degenerate cases)."""
    pool = CutPool(nodes={0, 1, 2, 3})
    assert pool.add([]) is None, "Empty cut (no nodes) should be rejected (return None)"
    assert pool.add([0, 1, 2, 3]) is None, (
        "Full cut (all nodes) should be rejected (return None)"
    )
    assert len(pool) == 0, (
        f"After rejecting both invalid cuts, pool should be empty, got size {len(pool)}"
    )


def test_all_returns_sorted_by_length_then_lex():
    """all() should return cuts sorted by (length, lex) for deterministic iteration."""
    pool = CutPool(nodes=set(range(10)))
    pool.add([5, 6, 7, 8, 9])  # canonical: {0,1,2,3,4} (size 5)
    pool.add([0, 1])  # canonical: {0,1} (size 2)
    pool.add([3, 4, 5])  # canonical: {3,4,5} (size 3)
    cuts = pool.all()
    sizes = [len(c) for c in cuts]
    assert sizes == [2, 3, 5], (
        f"Cuts should be sorted by (length, lex): expected sizes [2, 3, 5], got {sizes}"
    )


# --- Property tests (hypothesis) ---
#
# Each test uses `nodes_and_subtour` (a single `@st.composite`) which
# returns `(nodes, s)` as a tuple. The test unpacks the pair at the top.


@given(args=nodes_and_subtour())
@settings(max_examples=100)
def test_canonical_is_smaller_side(args):
    """Canonical form is always the smaller of S and V\\S."""
    nodes, s = args
    pool = CutPool(nodes=nodes)
    canonical = pool.add(s)
    complement = nodes - s
    assert canonical is not None, (
        f"add(s={set(s)}) should not be None for valid subtour"
    )
    assert len(canonical) <= len(complement), (
        f"Canonical {set(canonical)} (size {len(canonical)}) should be no larger "
        f"than complement {set(complement)} (size {len(complement)})"
    )


@given(args=nodes_and_subtour())
@settings(max_examples=100)
def test_add_is_idempotent(args: tuple[frozenset[int], frozenset[int]]):
    """Adding the same cut twice yields the same canonical and pool size 1."""
    nodes, s = args
    pool = CutPool(nodes=nodes)
    c1 = pool.add(s)
    c2 = pool.add(s)
    assert c1 is not None, f"add(s={set(s)}) should not be None for valid subtour"
    assert c2 is not None, f"add(s={set(s)}) should not be None for valid subtour"
    assert c1 == c2, f"add() should be idempotent: got c1={set(c1)}, c2={set(c2)}"
    assert len(pool) == 1, (
        f"After 2 identical adds, pool should have size 1, got {len(pool)}"
    )


@given(args=nodes_and_subtour())
@settings(max_examples=100)
def test_complement_collapses_with_original(
    args: tuple[frozenset[int], frozenset[int]],
):
    """Adding a cut and its complement yields a pool of size 1."""
    nodes, s = args
    pool = CutPool(nodes=nodes)
    pool.add(s)
    pool.add(nodes - s)
    assert len(pool) == 1, (
        f"Cut and its complement should collapse to 1 entry, got {len(pool)}"
    )


@given(args=nodes_and_subtour())
@settings(max_examples=100)
def test_add_accepts_any_iterable_form(args: tuple[frozenset[int], frozenset[int]]):
    """set / list / frozenset / reversed all yield the same canonical."""
    nodes, s = args
    p1 = CutPool(nodes=nodes)
    p1.add(s)
    p2 = CutPool(nodes=nodes)
    p2.add(list(s))
    p3 = CutPool(nodes=nodes)
    p3.add(sorted(s, reverse=True))
    assert p1._cuts == p2._cuts == p3._cuts, (
        f"Iterable form should not matter: {p1._cuts} vs {p2._cuts} vs {p3._cuts}"
    )


@given(args=nodes_and_subtour())
@settings(max_examples=100)
def test_contains_works_for_input_variants(args: tuple[frozenset[int], frozenset[int]]):
    """A cut can be looked up using any iterable form."""
    nodes, s = args
    pool = CutPool(nodes=nodes)
    pool.add(s)
    assert s in pool, f"After adding {set(s)}, it should be in the pool"
    assert nodes - s in pool, f"Complement {set(nodes - s)} should be in the pool"
    assert list(s) in pool, f"List form {list(s)} should be in the pool"
    assert frozenset(s) in pool, (
        f"Frozenset form {set(frozenset(s))} should be in the pool"
    )


@given(args=nodes_and_subtour())
@settings(max_examples=100)
def test_size_constant_under_repeated_add(args: tuple[frozenset[int], frozenset[int]]):
    """Adding the same cut 10 times still results in a pool of size 1."""
    nodes, s = args
    pool = CutPool(nodes=nodes)
    for _ in range(10):
        pool.add(s)
    assert len(pool) == 1, (
        f"After 10 identical adds, pool should have size 1, got {len(pool)}"
    )
