from collections import defaultdict

from ._helpers import Registry
from .constants import OrderType, Phase


reconcile = Registry()


@reconcile.register(Phase.DIPLOMACY)
def diplomacy(orders):
    by_id = {order["id"]: order for order in orders}

    def moving(src, dst=None):
        order = by_id.get(src)
        return order is not None and order["type"] == OrderType.MOVE and dst in (None, order["dst"])

    def convoying(fleet, src, dst):
        order = by_id.get(fleet)
        return order is not None and order["type"] == OrderType.CONVOY and (order["src"], order["dst"]) == (src, dst)

    for order in orders:
        if order["type"] == OrderType.SUPPORT_HOLD:
            order["failed"] = moving(order["dst"])
        elif order["type"] == OrderType.SUPPORT_MOVE:
            order["failed"] = not moving(order["src"], order["dst"])
        elif order["type"] == OrderType.CONVOY:
            order["failed"] = not (moving(order["src"], order["dst"]) and by_id[order["src"]].get("through", False))
        elif order["type"] == OrderType.MOVE and order.get("through", False):
            order["routes"] = [
                route for route in order["routes"]
                if all(convoying(fleet, order["id"], order["dst"]) for fleet in route)
            ]
            order["failed"] = not order["routes"]


@reconcile.register(Phase.RETREATS)
def retreats(orders):
    contenders = defaultdict(list)
    for order in orders:
        if order["type"] == OrderType.RETREAT:
            contenders[order["dst"]].append(order)
    for bounced in (group for group in contenders.values() if len(group) > 1):
        for order in bounced:
            order["failed"] = True
