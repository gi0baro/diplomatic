from collections import defaultdict

from ._diplomatico import solve_diplomacy
from ._helpers import Registry
from .constants import OrderType, Phase, Season, Troop
from .reconcile import reconcile


class Turn:
    __slots__ = ["phase", "year", "season", "territories", "build_centers", "centers_to_win"]

    def __init__(self, phase, year, season, territories, build_centers, centers_to_win):
        self.phase = phase
        self.year = year
        self.season = season
        self.territories = territories
        self.build_centers = {country: set(centers) for country, centers in build_centers.items()}
        self.centers_to_win = centers_to_win


class Outcome:
    __slots__ = [
        "orders", "succeeded", "dislodged", "positions", "coast_positions", "territories",
        "phase", "year", "season", "new_orders", "winner",
    ]

    def __init__(
        self, *, orders, succeeded, dislodged, positions, coast_positions, territories,
        phase, year, season, new_orders, winner,
    ):
        self.orders = orders
        self.succeeded = succeeded
        self.dislodged = dislodged
        self.positions = positions
        self.coast_positions = coast_positions
        self.territories = territories
        self.phase = phase
        self.year = year
        self.season = season
        self.new_orders = new_orders
        self.winner = winner


process = Registry()


def _flatten(orders):
    return [
        {
            "id": int(territory),
            "country": country,
            "type": order["type"],
            "src": int(order.get("src", 0)),
            "dst": int(order.get("dst", 0)),
            "through": order.get("through", False),
            "routes": [[int(fleet) for fleet in route] for route in order.get("routes", [])],
            "failed": order.get("failed", False),
        }
        for country, country_orders in orders.items()
        for territory, order in country_orders.items()
    ]


def _reconcile(phase, orders):
    entries = _flatten(orders)
    reconcile(phase, entries)
    for entry in entries:
        order = orders[entry["country"]][str(entry["id"])]
        order["failed"] = entry["failed"]
        if entry["through"]:
            order["routes"] = [[str(fleet) for fleet in route] for route in entry["routes"]]


def _adjudicate(orders):
    owners = {int(territory): country for country, country_orders in orders.items() for territory in country_orders}
    succeeded, dislodged = [], defaultdict(list)
    for verdict in solve_diplomacy(_flatten(orders)):
        country, territory = owners[verdict["id"]], str(verdict["id"])
        if verdict["succeeded"]:
            succeeded.append((country, territory))
        elif verdict["dislodged"]:
            dislodged[country].append(territory)
    return succeeded, dict(dislodged)


def _positions(board):
    positions = {
        country: {kind: list(units) for kind, units in troops.items()} for country, troops in board.troops.items()
    }
    return positions, dict(board.coast_positions)


def _move(board, positions, coasts, movements):
    for country, src, dst, coast in movements:
        kind = "fleets" if src in board.troops[country]["fleets"] else "armies"
        if kind == "fleets" and coast is not None:
            coasts[dst] = coast
        positions[country][kind].remove(src)
        positions[country][kind].append(dst)
    fleets = {fleet for troops in positions.values() for fleet in troops["fleets"]}
    for territory in set(coasts) - fleets:
        del coasts[territory]


def _disband(positions, disbands):
    for country, territories in disbands.items():
        for kind in ("armies", "fleets"):
            positions[country][kind] = [unit for unit in positions[country][kind] if unit not in territories]


def _build(positions, coasts, orders):
    for country, country_orders in orders.items():
        for territory, order in country_orders.items():
            if order["type"] != OrderType.BUILD:
                continue
            if order.get("troop") == Troop.ARMY:
                positions[country]["armies"].append(territory)
                continue
            positions[country]["fleets"].append(territory)
            if order.get("coast") is not None:
                coasts[territory] = order["coast"]


def _territories(board, turn, positions):
    territories = {country: list(owned) for country, owned in turn.territories.items()}
    for country, troops in positions.items():
        occupied = set(troops["armies"] + troops["fleets"]) - board.seas
        if turn.season == Season.SPRING:
            occupied -= board.supply_centers
        taken = occupied - set(territories[country])
        territories[country].extend(taken)
        for other in territories:
            if other != country:
                territories[other] = [territory for territory in territories[other] if territory not in taken]
    return territories


def _next_turn(turn, dislodged):
    if turn.phase == Phase.BUILDS:
        return Phase.DIPLOMACY, turn.year + 1, Season.SPRING
    if turn.phase == Phase.DIPLOMACY and dislodged:
        return Phase.RETREATS, turn.year, turn.season
    if turn.season == Season.SPRING:
        return Phase.DIPLOMACY, turn.year, Season.AUTUMN
    return Phase.BUILDS, turn.year, turn.season


def _active_countries(board, phase, positions, territories, dislodged):
    if phase == Phase.DIPLOMACY:
        return list(positions)
    if phase == Phase.RETREATS:
        return list(dislodged)
    return [
        country for country, troops in positions.items()
        if len(troops["armies"]) + len(troops["fleets"]) != len(board.supply_centers & set(territories[country]))
    ]


def _new_orders(board, turn, phase, countries, positions, territories, dislodged):
    if phase == Phase.DIPLOMACY:
        return {
            country: {unit: {"type": OrderType.HOLD} for units in positions[country].values() for unit in units}
            for country in countries
        }
    if phase == Phase.RETREATS:
        return {country: {unit: {"type": OrderType.DISBAND} for unit in dislodged[country]} for country in countries}
    new_orders = {}
    for country in countries:
        centers = board.supply_centers & set(territories[country])
        units = positions[country]["armies"] + positions[country]["fleets"]
        if len(centers) > len(units):
            units = (turn.build_centers[country] & set(territories[country])) - set(units)
        new_orders[country] = {unit: {"type": OrderType.HOLD} for unit in units}
    return new_orders


def _winner(board, turn, territories):
    counts = {country: len(board.supply_centers & set(owned)) for country, owned in territories.items()}
    best = max(counts.values(), default=0)
    if best < turn.centers_to_win:
        return None
    leaders = [country for country, count in counts.items() if count == best]
    return leaders[0] if len(leaders) == 1 else None


def _outcome(orders, board, turn, succeeded, dislodged, positions, coasts, territories):
    phase, year, season = _next_turn(turn, dislodged)
    countries = _active_countries(board, phase, positions, territories, dislodged)
    return Outcome(
        orders=orders,
        succeeded=succeeded,
        dislodged=dislodged,
        positions=positions,
        coast_positions=coasts,
        territories=territories,
        phase=phase,
        year=year,
        season=season,
        new_orders=_new_orders(board, turn, phase, countries, positions, territories, dislodged),
        winner=_winner(board, turn, territories) if phase == Phase.BUILDS else None,
    )


@process.register(Phase.DIPLOMACY)
def diplomacy(orders, board, turn):
    for country_orders in orders.values():
        for territory, order in country_orders.items():
            if order["type"] == OrderType.MOVE and order.get("through"):
                order["routes"] = board.convoy_routes(territory, order["dst"])
    _reconcile(Phase.DIPLOMACY, orders)
    succeeded, dislodged = _adjudicate(orders)
    movements = []
    for country, territory in succeeded:
        order = orders[country][territory]
        if order["type"] == OrderType.MOVE:
            movements.append((country, territory, order["dst"], order.get("coast")))
    positions, coasts = _positions(board)
    _move(board, positions, coasts, movements)
    territories = _territories(board, turn, positions)
    return _outcome(orders, board, turn, succeeded, dislodged, positions, coasts, territories)


@process.register(Phase.RETREATS)
def retreats(orders, board, turn):
    _reconcile(Phase.RETREATS, orders)
    succeeded, disbands, movements = [], defaultdict(list), []
    for country, country_orders in orders.items():
        for territory, order in country_orders.items():
            if order["type"] == OrderType.HOLD:
                country_orders[territory] = order = {"type": OrderType.DISBAND}
            if order["type"] == OrderType.RETREAT:
                if order.get("failed", False):
                    disbands[country].append(territory)
                    continue
                movements.append((country, territory, order["dst"], order.get("coast")))
            else:
                disbands[country].append(territory)
            succeeded.append((country, territory))
    positions, coasts = _positions(board)
    _disband(positions, disbands)
    _move(board, positions, coasts, movements)
    territories = _territories(board, turn, positions)
    return _outcome(orders, board, turn, succeeded, {}, positions, coasts, territories)


@process.register(Phase.BUILDS)
def builds(orders, board, turn):
    for country, country_orders in orders.items():
        units = board.troops[country]["armies"] + board.troops[country]["fleets"]
        owed = len(units) - len(board.supply_centers & set(turn.territories[country]))
        disbanding = [territory for territory, order in country_orders.items() if order["type"] == OrderType.DISBAND]
        others = [territory for territory, order in country_orders.items() if order["type"] != OrderType.DISBAND]
        for territory in others[:max(owed - len(disbanding), 0)]:
            country_orders[territory] = {"type": OrderType.DISBAND}
    succeeded = [(country, territory) for country, country_orders in orders.items() for territory in country_orders]
    positions, coasts = _positions(board)
    _build(positions, coasts, orders)
    _disband(positions, {
        country: [territory for territory, order in country_orders.items() if order["type"] == OrderType.DISBAND]
        for country, country_orders in orders.items()
    })
    territories = {country: list(owned) for country, owned in turn.territories.items()}
    return _outcome(orders, board, turn, succeeded, {}, positions, coasts, territories)
