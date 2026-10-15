from diplomatico import Board, Turn, process
from diplomatico.constants import OrderType, Phase, Season, Troop


# coasts 1, 2, 3 and the two-coasted 4 around seas 7, 8, 9; 5 is inland, 6 is neutral
MAP = {
    "seas": ["7", "8", "9"],
    "coasts": ["1", "2", "3", "4"],
    "neutrals": ["6"],
    "multi_coasts": {"4": [{}, {}]},
    "supply_centers": ["1", "2", "3", "4", "5"],
    "home_centers": {"x": ["1", "2"], "y": ["3", "4"]},
    "scs_to_win": 3,
    "links": {
        "armies": {"1": ["2", "5"], "2": ["1", "3", "4", "5"], "3": ["2", "4"], "4": ["2", "3"], "5": ["1", "2", "6"]},
        "fleets": {
            "1": ["7"],
            "2": ["4", "7", "8"],
            "3": ["4", "8", "9"],
            "4": ["2", "3", "8"],
            "7": ["1", "2", "8"],
            "8": ["2", "3", "4", "7", "9"],
            "9": ["3", "8"],
        },
        "multi_coasts": {"4": [{"2": None, "8": None}, {"3": None, "8": None}]},
    },
}


def order(type, **data):
    return {"type": type, **data}


def run(phase, season, orders, troops, territories, coasts=None):
    board = Board(MAP, troops, coasts or {})
    turn = Turn(phase, 1901, season, territories, MAP["home_centers"], MAP["scs_to_win"])
    return process(phase, orders, board, turn)


def test_spring_moves_do_not_capture_centers():
    outcome = run(
        Phase.DIPLOMACY, Season.SPRING,
        {"x": {"1": order(OrderType.MOVE, dst="2")}, "y": {"3": order(OrderType.HOLD)}},
        {"x": {"armies": ["1"], "fleets": []}, "y": {"armies": ["3"], "fleets": []}},
        {"x": ["1"], "y": ["3"]},
    )
    assert outcome.succeeded == [("x", "1"), ("y", "3")]
    assert outcome.positions == {"x": {"armies": ["2"], "fleets": []}, "y": {"armies": ["3"], "fleets": []}}
    assert outcome.territories == {"x": ["1"], "y": ["3"]}
    assert (outcome.phase, outcome.year, outcome.season) == (Phase.DIPLOMACY, 1901, Season.AUTUMN)
    assert outcome.new_orders == {"x": {"2": order(OrderType.HOLD)}, "y": {"3": order(OrderType.HOLD)}}
    assert outcome.winner is None


def test_convoy_routes_are_derived_from_the_board():
    outcome = run(
        Phase.DIPLOMACY, Season.SPRING,
        {"x": {
            "1": order(OrderType.MOVE, dst="3", through=True, routes=[]),
            "7": order(OrderType.CONVOY, src="1", dst="3"),
            "8": order(OrderType.CONVOY, src="1", dst="3"),
            "9": order(OrderType.HOLD),
        }},
        {"x": {"armies": ["1"], "fleets": ["7", "8", "9"]}},
        {"x": ["1"]},
    )
    assert outcome.orders["x"]["1"]["routes"] == [["7", "8"]]
    assert ("x", "1") in outcome.succeeded
    assert outcome.positions["x"]["armies"] == ["3"]


def test_dislodgements_open_a_retreat_phase():
    outcome = run(
        Phase.DIPLOMACY, Season.AUTUMN,
        {
            "x": {"1": order(OrderType.MOVE, dst="2"), "5": order(OrderType.SUPPORT_MOVE, src="1", dst="2")},
            "y": {"2": order(OrderType.HOLD)},
        },
        {"x": {"armies": ["1", "5"], "fleets": []}, "y": {"armies": ["2"], "fleets": []}},
        {"x": ["1", "5"], "y": ["2"]},
    )
    assert outcome.dislodged == {"y": ["2"]}
    assert outcome.positions["x"] == {"armies": ["5", "2"], "fleets": []}
    assert (outcome.phase, outcome.season) == (Phase.RETREATS, Season.AUTUMN)
    assert outcome.new_orders == {"y": {"2": order(OrderType.DISBAND)}}


def test_retreats_resolve_and_autumn_leads_to_builds():
    outcome = run(
        Phase.RETREATS, Season.AUTUMN,
        {"y": {"2": order(OrderType.RETREAT, dst="3")}},
        {"x": {"armies": ["5", "2"], "fleets": []}, "y": {"armies": ["2"], "fleets": []}},
        {"x": ["1", "5"], "y": ["3"]},
    )
    assert outcome.positions["y"] == {"armies": ["3"], "fleets": []}
    assert sorted(outcome.territories["x"]) == ["1", "2", "5"]
    assert (outcome.phase, outcome.year, outcome.season) == (Phase.BUILDS, 1901, Season.AUTUMN)
    assert outcome.new_orders == {"x": {"1": order(OrderType.HOLD)}}
    assert outcome.winner == "x"


def test_bounced_and_missing_retreats_disband():
    outcome = run(
        Phase.RETREATS, Season.SPRING,
        {"x": {"1": order(OrderType.RETREAT, dst="5"), "2": order(OrderType.HOLD)}, "y": {"3": order(OrderType.RETREAT, dst="5")}},
        {"x": {"armies": ["1", "2"], "fleets": []}, "y": {"armies": ["3"], "fleets": []}},
        {"x": [], "y": []},
    )
    assert outcome.orders["x"]["2"] == order(OrderType.DISBAND)
    assert outcome.succeeded == [("x", "2")]
    assert outcome.positions == {"x": {"armies": [], "fleets": []}, "y": {"armies": [], "fleets": []}}


def test_builds_apply_and_owed_disbands_are_forced():
    outcome = run(
        Phase.BUILDS, Season.AUTUMN,
        {
            "x": {"1": order(OrderType.BUILD, troop=Troop.ARMY), "4": order(OrderType.BUILD, troop=Troop.FLEET, coast=1)},
            "y": {"3": order(OrderType.HOLD), "8": order(OrderType.HOLD)},
        },
        {"x": {"armies": ["5", "2"], "fleets": []}, "y": {"armies": ["3"], "fleets": ["8"]}},
        {"x": ["1", "2", "4", "5"], "y": ["3"]},
    )
    assert outcome.positions == {"x": {"armies": ["5", "2", "1"], "fleets": ["4"]}, "y": {"armies": [], "fleets": ["8"]}}
    assert outcome.coast_positions == {"4": 1}
    assert outcome.orders["y"]["3"] == order(OrderType.DISBAND)
    assert (outcome.phase, outcome.year, outcome.season) == (Phase.DIPLOMACY, 1902, Season.SPRING)
    assert outcome.new_orders["y"] == {"8": order(OrderType.HOLD)}
