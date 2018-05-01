# -*- coding: utf-8 -*-

from diplomacy import GameProcessor
from .. import app


def process_game(game):
    map_data = {key: game.map[key] for key in ['seas', 'supply_centers', 'home_centers', 'scs_to_win', 'names']}
    current_phase = game.active_phase()
    orders = current_phase.orders_for_processor()
    print(orders)
    proc = GameProcessor(
        map_data, game.build_everywhere, current_phase.type, current_phase.year, current_phase.season,
        current_phase.troops, current_phase.territories, current_phase.coasts, logger=app.log.debug)
    ctx = proc.process(orders)
    updated_orders = {}
    for country, orders in ctx.orders.items():
        for territory, order in orders.items():
            data = {key: order[key] for key in set(order.keys()) - {'type', 'failed'}}
            updated_orders[territory] = {'type': order['type'], 'data': data}
    new_orders = {}
    for country, orders in ctx.new_orders.items():
        new_orders[country] = []
        for territory, order in orders.items():
            new_orders[country].append({'territory': territory, 'type': order['type']})
    successful_orders = [element[1] for element in ctx.succeeded]
    return ctx, updated_orders, new_orders, successful_orders
