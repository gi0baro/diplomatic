from diplomatico import Board


MAP = {
    "seas": ["s1", "s2", "s3"],
    "coasts": ["a", "b", "c"],
    "neutrals": [],
    "multi_coasts": {},
    "supply_centers": [],
    "links": {
        "fleets": {
            "a": ["s1"],
            "b": ["s1", "s2"],
            "c": ["s2", "s3"],
            "s1": ["a", "b", "s2"],
            "s2": ["b", "c", "s1", "s3"],
            "s3": ["c", "s2"],
        }
    },
}


def board(*fleets):
    return Board(MAP, {"x": {"armies": ["a"], "fleets": list(fleets)}}, {})


def test_every_chain_of_fleets_at_sea_is_a_route():
    assert sorted(board("s1", "s2", "s3").convoy_routes("a", "b")) == [["s1"], ["s1", "s2"]]
    assert sorted(board("s1", "s2", "s3").convoy_routes("a", "c")) == [["s1", "s2"], ["s1", "s2", "s3"]]


def test_chains_stop_at_empty_seas():
    assert board("s1", "s3").convoy_routes("a", "b") == [["s1"]]
    assert board("s1", "s3").convoy_routes("a", "c") == []


def test_fleets_on_coasts_do_not_convoy():
    assert board("s1", "b").convoy_routes("a", "c") == []


def test_chains_never_return_to_the_origin():
    assert board("s1", "s2", "s3").convoy_routes("a", "a") == []
