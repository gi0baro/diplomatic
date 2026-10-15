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


# the two-coasted p and q border each other west to west (coast 0) and east to east (coast 1)
PAIRED = {
    "seas": ["w", "e"],
    "coasts": ["p", "q"],
    "neutrals": [],
    "multi_coasts": ["p", "q"],
    "supply_centers": [],
    "links": {
        "fleets": {"p": ["w", "q", "e"], "q": ["w", "p", "e"], "w": ["p", "q"], "e": ["p", "q"]},
        "multi_coasts": {
            "p": [{"w": None, "q": [0]}, {"e": None, "q": [1]}],
            "q": [{"w": None, "p": [0]}, {"e": None, "p": [1]}],
        },
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


def test_a_coast_is_touched_from_the_paired_coast_only():
    paired = Board(PAIRED, {"x": {"armies": [], "fleets": ["p", "q", "w"]}}, {"p": 0, "q": 1})
    assert paired.touches_coast("p", "q", 0)
    assert not paired.touches_coast("p", "q", 1)
    assert paired.touches_coast("q", "p", 1)
    assert not paired.touches_coast("q", "p", 0)
    assert paired.touches_coast("w", "p", 0)
    assert not paired.touches_coast("w", "p", 1)


def test_a_fleet_on_a_multi_coast_province_moves_along_its_coast():
    paired = Board(PAIRED, {"x": {"armies": [], "fleets": ["p", "q"]}}, {"p": 0, "q": 1})
    assert paired.can_move("p", "w") and paired.can_move("p", "q")
    assert not paired.can_move("p", "e")
    assert paired.can_move("q", "e") and not paired.can_move("q", "w")
