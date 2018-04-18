# -*- coding: utf-8 -*-

from diplomacy import OrdersProcessor
from weppy import sdict
from .. import app, GamePhase


def process_order(country, game, territory, data):
    app.log.debug(game)
    app.log.debug(game.map)
    app.log.debug(game.map.name)
    current_phase = game.active_phase()
    previous_phase = game.phases.where(
        lambda m: m.stage == GamePhase.STAGES['closed']).select(orderby=~GamePhase.created_at, limitby=(0, 1)).first()
    map_data = {
        key: game.map[key] for key in [
            'seas', 'coasts', 'neutrals', 'multi_coasts', 'supply_centers', 'home_centers', 'links', 'names']}
    previous_orders = previous_phase.orders() if previous_phase else []
    player_troops = current_phase.troops[country]['armies'] + current_phase.troops[country]['fleets']
    proc = OrdersProcessor(
        map_data, game.build_everywhere, current_phase.type, current_phase.troops, current_phase.coasts, country,
        player_troops, current_phase.territories[country], previous_orders, logger=app.log.warning)
    orders, error = proc.process({territory: data})
    return orders[territory], error
