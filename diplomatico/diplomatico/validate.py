from collections import defaultdict

from ._helpers import Registry
from .constants import OrderType, Phase, Troop


validate = Registry()


def _rejections(orders, check):
    rejected = {}
    for territory, order in orders.items():
        reason = check(territory, order)
        if reason:
            rejected[territory] = reason
    return rejected


def _neutral(board, territory, order):
    if board.neutrals & {territory, order.get("src"), order.get("dst")}:
        return "neutral territory"


def _foreign(player, territory):
    if territory not in player.troops:
        return "not a player unit"


def _step(board, territory, order):
    dst = order["dst"]
    if not board.can_move(territory, dst):
        return "cannot move there"
    if territory not in board.fleets or dst not in board.multi_coasts:
        order.pop("coast", None)
        return None
    if order.get("coast") not in (0, 1):
        return "missing coast"
    if not board.touches_coast(territory, dst, order["coast"]):
        return "cannot reach that coast"


def _convoyed(board, territory, order):
    if territory in board.fleets:
        return "fleets cannot be convoyed"
    routes = board.convoy_routes(territory, order["dst"])
    if not routes:
        return "no convoy route"
    if any(route not in routes for route in order.get("routes", [])):
        return "unknown convoy route"


def _movement(board, territory, order):
    kind = order["type"]
    if kind == OrderType.HOLD:
        return None
    if kind not in (OrderType.MOVE, OrderType.SUPPORT_HOLD, OrderType.SUPPORT_MOVE, OrderType.CONVOY):
        return "invalid order type"
    if not order.get("dst"):
        return "missing destination"
    if kind in (OrderType.SUPPORT_MOVE, OrderType.CONVOY) and not order.get("src"):
        return "missing source"
    if kind == OrderType.MOVE:
        return _convoyed(board, territory, order) if order.get("through") else _step(board, territory, order)
    if kind == OrderType.CONVOY:
        return None if territory in board.fleets else "only fleets convoy"
    if not board.can_move(territory, order["dst"]):
        return "cannot reach the supported territory"
    if board.is_empty(order["src"] if kind == OrderType.SUPPORT_MOVE else order["dst"]):
        return "nothing to support"


@validate.register(Phase.DIPLOMACY)
def diplomacy(orders, board, player):
    return _rejections(orders, lambda territory, order: (
        _neutral(board, territory, order) or _foreign(player, territory) or _movement(board, territory, order)
    ))


def _retreat(board, contested, attackers, territory, order):
    kind = order["type"]
    if kind in (OrderType.HOLD, OrderType.DISBAND):
        return None
    if kind != OrderType.RETREAT:
        return "invalid order type"
    if not order.get("dst"):
        return "missing destination"
    reason = _step(board, territory, order)
    if reason:
        return reason
    if not board.is_empty(order["dst"]):
        return "occupied"
    if order["dst"] in contested:
        return "contested territory"
    if order["dst"] in attackers[territory]:
        return "attacker origin"


@validate.register(Phase.RETREATS)
def retreats(orders, board, player, previous_orders):
    contested = set()
    attackers = defaultdict(set)
    for country in previous_orders.values():
        for src, order in country.items():
            if order["type"] == OrderType.MOVE:
                contested.add(order["dst"])
                attackers[order["dst"]].add(src)
    return _rejections(orders, lambda territory, order: (
        _neutral(board, territory, order) or _foreign(player, territory)
        or _retreat(board, contested, attackers, territory, order)
    ))


def _build(board, player, territory, order):
    kind = order["type"]
    if kind == OrderType.HOLD:
        return None
    if kind == OrderType.DISBAND:
        return _foreign(player, territory)
    if kind != OrderType.BUILD:
        return "invalid order type"
    if order.get("troop") not in (Troop.ARMY, Troop.FLEET):
        return "unknown troop type"
    if not board.is_empty(territory):
        return "occupied"
    if territory not in player.build_centers & player.territories:
        return "not an available center"
    if order["troop"] == Troop.FLEET:
        if territory not in board.coasts:
            return "fleets need a coast"
        if territory in board.multi_coasts and order.get("coast") not in (0, 1):
            return "missing coast"


@validate.register(Phase.BUILDS)
def builds(orders, board, player):
    rejected = _rejections(orders, lambda territory, order: (
        _neutral(board, territory, order) or _build(board, player, territory, order)
    ))
    allowance = len(board.supply_centers & player.territories) - len(player.troops)
    due, undue = (OrderType.BUILD, OrderType.DISBAND) if allowance > 0 else (OrderType.DISBAND, OrderType.BUILD)
    for territory, order in orders.items():
        if territory not in rejected and order["type"] == undue:
            rejected[territory] = f"no {undue.name.lower()} allowed"
    pending = sorted(territory for territory, order in orders.items() if territory not in rejected and order["type"] == due)
    for territory in pending[abs(allowance):]:
        rejected[territory] = f"exceeds {due.name.lower()}s"
    return rejected
