"""TSPLIB loader: metric gate and coordinate parsing (local archive, no HiGHS)."""

import pytest
from examples.tsplib import TspLibGraphInstanceDb


@pytest.fixture(scope="module")
def db() -> TspLibGraphInstanceDb:
    return TspLibGraphInstanceDb()


def test_loader_rejects_non_euc_2d(db: TspLibGraphInstanceDb) -> None:
    # att48 is ATT (pseudo-Euclidean): plain rounded distances would not
    # match its certified optimum, so the loader must refuse it.
    with pytest.raises(ValueError, match="EDGE_WEIGHT_TYPE") as exc:
        db["att48"]
    assert "ATT" in str(exc.value), f"error should name the metric: {exc.value}"


def test_loader_parses_padded_coordinates(db: TspLibGraphInstanceDb) -> None:
    # rat99 pads its columns ("  1  6  4"); split(" ") used to reject it.
    g = db["rat99"]
    assert g.number_of_nodes() == 99, f"expected 99 nodes, got {g.number_of_nodes()}"
    assert g.number_of_edges() == 99 * 98 // 2, (
        f"expected complete graph, got {g.number_of_edges()} edges"
    )
    assert g.nodes[0]["pos"] == (6.0, 4.0), (
        f"first city should be (6, 4), got {g.nodes[0]['pos']}"
    )


def test_whitelist_names_all_load(db: TspLibGraphInstanceDb) -> None:
    # Every advertised instance must pass the metric gate and the parser.
    for name in db:
        g = db[name]
        assert g.number_of_nodes() > 0, f"{name} loaded an empty graph"
