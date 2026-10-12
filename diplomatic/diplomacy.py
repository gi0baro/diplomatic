from diplomatico.constants import Phase

from diplomatico import Board, Player, Turn, process, validate


def process_order(country, game, territory, data):
    phase = game.active_phase()
    board = Board(game.map, phase.troops, phase.coasts)
    troops = phase.troops[country]
    player = Player(
        troops["armies"] + troops["fleets"],
        phase.territories[country],
        game.map.supply_centers if game.build_everywhere else game.map.home_centers[country],
    )
    orders = phase.orders_for_processor()[country]
    orders[territory] = data
    if phase.type == Phase.RETREATS:
        previous = phase.parent.orders_for_processor() if phase.parent else {}
        rejected = validate(phase.type, orders, board, player, previous)
    else:
        rejected = validate(phase.type, orders, board, player)
    return orders[territory], rejected


def process_game(game):
    phase = game.active_phase()
    board = Board(game.map, phase.troops, phase.coasts)
    build_centers = {
        country: game.map.supply_centers if game.build_everywhere else centers
        for country, centers in game.map.home_centers.items()
    }
    turn = Turn(
        phase.type, phase.year, phase.season, phase.territories, build_centers, game.target_sc or game.map.scs_to_win
    )
    outcome = process(phase.type, phase.orders_for_processor(), board, turn)
    updated_orders = {}
    for country_orders in outcome.orders.values():
        for territory, order in country_orders.items():
            data = {key: value for key, value in order.items() if key not in ("type", "failed")}
            updated_orders[territory] = {"type": order["type"], "data": data}
    new_orders = {
        country: [{"territory": territory, "type": order["type"]} for territory, order in country_orders.items()]
        for country, country_orders in outcome.new_orders.items()
    }
    successful_orders = [territory for _, territory in outcome.succeeded]
    return outcome, updated_orders, new_orders, successful_orders
