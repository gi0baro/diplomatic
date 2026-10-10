from diplomatico import Board, Player, validate
from diplomatico.constants import OrderType, Phase, Troop


# coasts a, b, c and the two-coasted m around seas s1, s2, s3; i is inland, n is neutral
MAP = {
    "seas": ["s1", "s2", "s3"],
    "coasts": ["a", "b", "c", "m"],
    "neutrals": ["n"],
    "multi_coasts": {"m": [{}, {}]},
    "supply_centers": ["a", "b", "c", "i", "m"],
    "links": {
        "armies": {"a": ["b", "i"], "b": ["a", "c", "i", "m"], "c": ["b", "m"], "i": ["a", "b", "n"], "m": ["b", "c"]},
        "fleets": {
            "a": ["s1"],
            "b": ["s1", "s2", "m"],
            "c": ["s2", "s3", "m"],
            "m": ["b", "c", "s2"],
            "s1": ["a", "b", "s2"],
            "s2": ["b", "c", "m", "s1", "s3"],
            "s3": ["c", "s2"],
        },
        "multi_coasts": {"m": [["b", "s2"], ["c", "s2"]]},
    },
}


def board(armies=(), fleets=(), coasts=None):
    return Board(MAP, {"x": {"armies": list(armies), "fleets": list(fleets)}}, coasts or {})


def player(troops=(), territories=(), build_centers=()):
    return Player(troops, territories, build_centers)


def order(type, **data):
    return {"type": type, **data}


def test_orders_touching_neutrals_or_foreign_units_are_rejected():
    orders = {
        "a": order(OrderType.MOVE, dst="n"),
        "b": order(OrderType.HOLD),
        "c": order(OrderType.HOLD),
    }
    rejected = validate(Phase.DIPLOMACY, orders, board(armies=["a", "b", "c"]), player(troops=["a", "b"]))
    assert rejected == {"a": "neutral territory", "c": "not a player unit"}


def test_moves_follow_unit_adjacency():
    orders = {
        "a": order(OrderType.MOVE, dst="b"),
        "b": order(OrderType.MOVE, dst="s1"),
        "c": order(OrderType.MOVE, dst="s2"),
        "s3": order(OrderType.MOVE, dst="b"),
        "s2": order(OrderType.HOLD, dst="b"),
    }
    rejected = validate(
        Phase.DIPLOMACY, orders, board(armies=["a", "b"], fleets=["c", "s2", "s3"]),
        player(troops=["a", "b", "c", "s2", "s3"]),
    )
    assert rejected == {"b": "cannot move there", "s3": "cannot move there"}


def test_fleets_move_between_specific_coasts():
    orders = {
        "s2": order(OrderType.MOVE, dst="m", coast=0),
        "s1": order(OrderType.MOVE, dst="m", coast=0),
        "b": order(OrderType.MOVE, dst="m"),
        "c": order(OrderType.MOVE, dst="m", coast=0),
        "m": order(OrderType.MOVE, dst="b"),
        "a": order(OrderType.MOVE, dst="b", coast=1),
    }
    rejected = validate(
        Phase.DIPLOMACY, orders, board(armies=["a"], fleets=["s1", "s2", "b", "c", "m"], coasts={"m": 1}),
        player(troops=["a", "b", "c", "m", "s1", "s2"]),
    )
    assert rejected == {
        "s1": "cannot move there",
        "b": "missing coast",
        "c": "cannot reach that coast",
        "m": "cannot move there",
    }
    assert "coast" not in orders["a"]


def test_convoyed_moves_need_an_existing_route():
    orders = {
        "a": order(OrderType.MOVE, dst="c", through=True, routes=[["s1", "s2"]]),
        "b": order(OrderType.MOVE, dst="c", through=True, routes=[["s1"]]),
        "s3": order(OrderType.MOVE, dst="a", through=True),
        "c": order(OrderType.MOVE, dst="i", through=True),
    }
    rejected = validate(
        Phase.DIPLOMACY, orders, board(armies=["a", "b", "c"], fleets=["s1", "s2", "s3"]),
        player(troops=["a", "b", "c", "s3"]),
    )
    assert rejected == {"b": "unknown convoy route", "s3": "fleets cannot be convoyed", "c": "no convoy route"}
    assert orders["a"]["routes"] == [["s1", "s2"]]


def test_supports_and_convoys_need_a_reachable_and_occupied_target():
    orders = {
        "a": order(OrderType.SUPPORT_HOLD, dst="c"),
        "b": order(OrderType.SUPPORT_HOLD, dst="i"),
        "c": order(OrderType.SUPPORT_MOVE, src="a", dst="b"),
        "m": order(OrderType.CONVOY, src="a", dst="c"),
        "s1": order(OrderType.SUPPORT_MOVE, dst="b"),
        "s2": order(OrderType.SUPPORT_MOVE, src="i", dst="b"),
        "s3": order(OrderType.CONVOY, src="a", dst="c"),
        "n": order(OrderType.RETREAT, dst="i"),
    }
    rejected = validate(
        Phase.DIPLOMACY, orders, board(armies=["a", "b", "c", "m"], fleets=["s1", "s2", "s3"]),
        player(troops=["a", "b", "c", "m", "s1", "s2", "s3"]),
    )
    assert rejected == {
        "a": "cannot reach the supported territory",
        "b": "nothing to support",
        "m": "only fleets convoy",
        "s1": "missing source",
        "s2": "nothing to support",
        "n": "neutral territory",
    }


def test_movement_orders_need_a_valid_type_and_a_destination():
    orders = {"a": order(OrderType.RETREAT, dst="b"), "b": order(OrderType.MOVE)}
    rejected = validate(Phase.DIPLOMACY, orders, board(armies=["a", "b"]), player(troops=["a", "b"]))
    assert rejected == {"a": "invalid order type", "b": "missing destination"}


def test_retreats_avoid_occupied_contested_and_attacker_territories():
    previous = {"y": {"b": order(OrderType.MOVE, dst="a"), "c": order(OrderType.MOVE, dst="i")}}
    orders = {
        "a": order(OrderType.RETREAT, dst="i"),
        "m": order(OrderType.RETREAT, dst="c"),
        "s2": order(OrderType.RETREAT, dst="s1"),
    }
    rejected = validate(
        Phase.RETREATS, orders, board(armies=["a", "m", "c"], fleets=["s2"]), player(troops=["a", "m", "s2"]), previous,
    )
    assert rejected == {"a": "contested territory", "m": "occupied"}

    orders = {"a": order(OrderType.RETREAT, dst="b")}
    rejected = validate(Phase.RETREATS, orders, board(armies=["a"]), player(troops=["a"]), previous)
    assert rejected == {"a": "attacker origin"}


def test_retreat_orders_are_retreats_disbands_or_holds():
    orders = {
        "a": order(OrderType.DISBAND),
        "b": order(OrderType.RETREAT),
        "c": order(OrderType.MOVE, dst="b"),
        "i": order(OrderType.HOLD),
        "s2": order(OrderType.RETREAT, dst="m"),
    }
    rejected = validate(
        Phase.RETREATS, orders, board(armies=["a", "b", "c", "i"], fleets=["s2"]),
        player(troops=["a", "b", "c", "i", "s2"]), {},
    )
    assert rejected == {"b": "missing destination", "c": "invalid order type", "s2": "missing coast"}


def test_builds_go_on_free_owned_build_centers():
    orders = {
        "b": order(OrderType.BUILD, troop=Troop.ARMY),
        "c": order(OrderType.BUILD, troop=Troop.FLEET),
        "i": order(OrderType.BUILD, troop=Troop.FLEET),
        "m": order(OrderType.BUILD, troop=Troop.FLEET),
        "a": order(OrderType.BUILD, troop="army"),
    }
    rejected = validate(
        Phase.BUILDS, orders, board(armies=["c"]),
        player(territories=["a", "b", "c", "i", "m"], build_centers=["a", "b", "i", "m"]),
    )
    assert rejected == {
        "c": "occupied",
        "i": "fleets need a coast",
        "m": "missing coast",
        "a": "unknown troop type",
    }

    orders = {"c": order(OrderType.BUILD, troop=Troop.ARMY), "m": order(OrderType.BUILD, troop=Troop.FLEET, coast=1)}
    rejected = validate(
        Phase.BUILDS, orders, board(), player(territories=["a", "b", "c", "m"], build_centers=["a", "b", "m"]),
    )
    assert rejected == {"c": "not an available center"}


def test_build_allowance_caps_the_sorted_builds():
    orders = {
        "b": order(OrderType.BUILD, troop=Troop.ARMY),
        "c": order(OrderType.BUILD, troop=Troop.ARMY),
        "i": order(OrderType.BUILD, troop=Troop.ARMY),
        "a": order(OrderType.DISBAND),
    }
    rejected = validate(
        Phase.BUILDS, orders, board(armies=["a"], fleets=["s1"]),
        player(troops=["a", "s1"], territories=["a", "b", "c", "i"], build_centers=["a", "b", "c", "i"]),
    )
    assert rejected == {"i": "exceeds builds", "a": "no disband allowed"}


def test_disband_requirement_caps_the_sorted_disbands():
    orders = {
        "a": order(OrderType.DISBAND),
        "b": order(OrderType.DISBAND),
        "c": order(OrderType.DISBAND),
        "s1": order(OrderType.DISBAND),
        "i": order(OrderType.BUILD, troop=Troop.ARMY),
    }
    rejected = validate(
        Phase.BUILDS, orders, board(armies=["a", "b", "c"], fleets=["s1"]),
        player(troops=["a", "b", "c"], territories=["a", "i"], build_centers=["a", "i"]),
    )
    assert rejected == {
        "b": "exceeds disbands",
        "c": "exceeds disbands",
        "s1": "not a player unit",
        "i": "no build allowed",
    }
