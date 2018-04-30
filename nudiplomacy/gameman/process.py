# -*- coding: utf-8 -*-

from diplomacy import GameProcessor
from weppy import sdict
from .. import app, GamePhase


def process_game(game):
    map_data = {key: game.map[key] for key in ['seas', 'supply_centers', 'home_centers', 'scs_to_win', 'names']}
    current_phase = game.active_phase()
    orders = current_phase.orders_for_processor()
    print(orders)
    proc = GameProcessor(
        map_data, game.build_everywhere, current_phase.type, current_phase.year, current_phase.season,
        current_phase.troops, current_phase.territories, current_phase.coasts, logger=app.log.debug)
    ctx = proc.process(orders)
    print(ctx)
    return ctx
