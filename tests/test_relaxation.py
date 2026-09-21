import pytest
from tsp_bnb import BranchingDecisions, CutPool, LPRelaxation, TSPInstance
from tsp_bnb.branching_decisions import edge_index_of
from tsp_bnb.relaxed_solution import SolveStatus

pytestmark = pytest.mark.slow


def test_solve_on_empty_returns_optimal(
    square_instance: TSPInstance,
    fresh_pool: CutPool,
    empty_decisions: BranchingDecisions,
):
    """A complete 4-city graph with no fixations should solve to OPTIMAL."""
    solver = LPRelaxation(square_instance, empty_decisions, cut_pool=fresh_pool)
    sol = solver.solve()
    assert sol.status == SolveStatus.OPTIMAL, f"Expected OPTIMAL, got {sol.status}"
    assert sol.lower_bound > 0, f"Lower bound should be positive, got {sol.lower_bound}"
    assert sol.basis is not None, "Solver should capture the basis for warm-starting"


def test_solve_respects_fixations(square_instance: TSPInstance, fresh_pool: CutPool):
    """Fixing an edge to 1 forces it to 1.0 in the LP solution."""
    decisions = BranchingDecisions(square_instance.graph.number_of_edges())
    edge_idx = edge_index_of(square_instance.graph.edges, 0, 1)
    decisions.fix(edge_idx, 1)
    solver = LPRelaxation(square_instance, decisions, cut_pool=fresh_pool)
    sol = solver.solve()
    assert sol.status == SolveStatus.OPTIMAL, f"Expected OPTIMAL, got {sol.status}"
    assert sol.edge_fractions[edge_idx] == pytest.approx(1.0, abs=1e-6), (
        f"Edge (0, 1) at index {edge_idx} should be fixed to 1.0, "
        f"got {sol.edge_fractions[edge_idx]}"
    )


def test_solve_infeasible_when_node_degree_unsatisfiable(
    square_instance: TSPInstance,
    fresh_pool: CutPool,
):
    """Fixing all edges incident to node 0 to 0 violates the degree constraint."""
    decisions = BranchingDecisions(square_instance.graph.number_of_edges())
    for u, v in square_instance.graph.edges(0):
        decisions.fix(edge_index_of(square_instance.graph.edges, u, v), 0)
    solver = LPRelaxation(square_instance, decisions, cut_pool=fresh_pool)
    sol = solver.solve()
    assert sol.status == SolveStatus.INFEASIBLE, (
        f"Expected INFEASIBLE (no edges at node 0), got {sol.status}"
    )
    assert sol.is_infeasible(), (
        "is_infeasible() should return True for INFEASIBLE solutions"
    )


def test_cut_pool_grows_during_solve(
    two_triangles_instance: TSPInstance,
):
    """SECs discovered by separation get added to the shared pool.

    Degree-only LP on two triangles = two disconnected subtours; separation
    must add the SEC. Pool grows to exactly 1: {0,1,2} and its complement
    {3,4,5} canonicalize to the same cut.
    """
    pool = CutPool(nodes=two_triangles_instance.graph.nodes)
    decisions = BranchingDecisions(two_triangles_instance.graph.number_of_edges())
    solver = LPRelaxation(two_triangles_instance, decisions, cut_pool=pool)
    assert len(pool) == 0, f"Pool should be empty before solve, got size {len(pool)}"
    solver.solve()
    assert len(pool) == 1, (
        f"Pool should hold the one canonical SEC after solve, got {len(pool)}"
    )


def test_square_lp_is_integral_so_pool_stays_empty(
    square_instance: TSPInstance,
    fresh_pool: CutPool,
    empty_decisions: BranchingDecisions,
):
    """Square degree-only LP optimum is the perimeter tour (cost 4.0): integral
    and connected, so separation finds nothing and no cuts are added."""
    solver = LPRelaxation(square_instance, empty_decisions, cut_pool=fresh_pool)
    sol = solver.solve()
    assert len(fresh_pool) == 0, (
        f"Integral LP needs no SECs, but pool has {len(fresh_pool)} cuts"
    )
    assert sol.is_integral(), (
        f"Square LP optimum should be the integral perimeter tour, "
        f"got fractions {[round(v, 3) for v in sol.edge_fractions]}"
    )
    assert sol.lower_bound == pytest.approx(4.0), (
        f"Square optimum is 4.0, got {sol.lower_bound}"
    )


def test_basis_can_be_threaded_to_child(
    square_instance: TSPInstance, fresh_pool: CutPool
):
    """Child solver using parent's basis solves without error."""
    root = LPRelaxation(
        square_instance,
        BranchingDecisions(square_instance.graph.number_of_edges()),
        cut_pool=fresh_pool,
    )
    root_sol = root.solve()
    assert root_sol.basis is not None, "Root solver should capture a basis"

    child_decisions = BranchingDecisions(square_instance.graph.number_of_edges())
    child_decisions.fix(edge_index_of(square_instance.graph.edges, 0, 1), 0)
    child = LPRelaxation(
        square_instance,
        child_decisions,
        cut_pool=fresh_pool,
        parent_basis=root_sol.basis,
    )
    child_sol = child.solve()
    assert child_sol.status == SolveStatus.OPTIMAL, (
        f"Child solver with parent basis should solve, got status {child_sol.status}"
    )


def test_two_independent_solvers_agree(square_instance: TSPInstance):
    """Same problem, two solvers, same lower bound."""
    pool1 = CutPool(square_instance.graph.nodes)
    pool2 = CutPool(square_instance.graph.nodes)
    decisions = BranchingDecisions(square_instance.graph.number_of_edges())
    s1 = LPRelaxation(square_instance, decisions, cut_pool=pool1).solve()
    s2 = LPRelaxation(square_instance, decisions, cut_pool=pool2).solve()
    assert s1.lower_bound == pytest.approx(s2.lower_bound, abs=1e-6), (
        f"Independent solvers should agree: got {s1.lower_bound} vs {s2.lower_bound}"
    )


def test_three_city_solves_integral(triangle_instance: TSPInstance):
    """3-city TSP LP is integral without cuts (smallest non-trivial)."""
    pool = CutPool(triangle_instance.graph.nodes)
    decisions = BranchingDecisions(triangle_instance.graph.number_of_edges())
    solver = LPRelaxation(triangle_instance, decisions, cut_pool=pool)
    sol = solver.solve()
    assert sol.status == SolveStatus.OPTIMAL, f"Expected OPTIMAL, got {sol.status}"
    assert sol.is_integral(), "3-city LP should be integral without cuts"
    assert sol.lower_bound == pytest.approx(3.0, abs=1e-6), (
        f"3-city TSP optimal tour is 3.0, got lower bound {sol.lower_bound}"
    )
