from diplomatico import reconcile
from diplomatico.constants import OrderType, Phase


def order(id, type, **data):
    return {"id": id, "country": "x", "type": type, "failed": False, **data}


def failed(orders):
    return {order["id"] for order in orders if order["failed"]}


def test_support_hold_on_moving_unit_fails():
    orders = [
        order(1, OrderType.MOVE, dst=3),
        order(2, OrderType.SUPPORT_HOLD, dst=1),
        order(4, OrderType.SUPPORT_HOLD, dst=5),
        order(5, OrderType.HOLD),
    ]
    reconcile(Phase.DIPLOMACY, orders)
    assert failed(orders) == {2}


def test_support_move_must_match_the_move():
    orders = [
        order(1, OrderType.MOVE, dst=3),
        order(2, OrderType.SUPPORT_MOVE, src=1, dst=3),
        order(4, OrderType.SUPPORT_MOVE, src=1, dst=5),
        order(6, OrderType.SUPPORT_MOVE, src=7, dst=3),
        order(7, OrderType.HOLD),
    ]
    reconcile(Phase.DIPLOMACY, orders)
    assert failed(orders) == {4, 6}


def test_convoy_needs_a_convoyed_move():
    orders = [
        order(1, OrderType.MOVE, dst=3, through=True, routes=[[10]]),
        order(10, OrderType.CONVOY, src=1, dst=3),
        order(2, OrderType.MOVE, dst=4),
        order(11, OrderType.CONVOY, src=2, dst=4),
        order(12, OrderType.CONVOY, src=1, dst=5),
    ]
    reconcile(Phase.DIPLOMACY, orders)
    assert failed(orders) == {11, 12}


def test_routes_are_pruned_to_convoying_fleets():
    orders = [
        order(1, OrderType.MOVE, dst=3, through=True, routes=[[10, 11], [12]]),
        order(10, OrderType.CONVOY, src=1, dst=3),
        order(11, OrderType.HOLD),
        order(12, OrderType.CONVOY, src=1, dst=3),
        order(2, OrderType.MOVE, dst=4, through=True, routes=[[13]]),
        order(13, OrderType.CONVOY, src=2, dst=5),
    ]
    reconcile(Phase.DIPLOMACY, orders)
    assert orders[0]["routes"] == [[12]]
    assert orders[4]["routes"] == []
    assert failed(orders) == {2, 13}


def test_retreats_into_the_same_territory_bounce():
    orders = [
        order(1, OrderType.RETREAT, dst=3),
        order(2, OrderType.RETREAT, dst=3),
        order(4, OrderType.RETREAT, dst=5),
        order(6, OrderType.DISBAND),
    ]
    reconcile(Phase.RETREATS, orders)
    assert failed(orders) == {1, 2}
