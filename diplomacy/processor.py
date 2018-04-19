# -*- coding: utf-8 -*-

from collections import defaultdict
from .checkers import PreProcessor
from .constants import ORDERS, PHASES
from .helpers import adict, registry
from .judge import Judge


class ProcessingPipeline(object):
    def __init__(self, *methods):
        self.methods = methods

    def process(self, orders):
        ctx = adict(orders=orders)
        for method in self.methods:
            method(ctx)
        return ctx


class GameProcessor(object):
    pipelines = registry()

    def __init__(
        self, map_data, allowed_supply_centers, phase_type, armies, fleets, multi_coasts_positions, player_troops,
        player_territories, previous_orders=[], logger=None
    ):
        self._logger = logger
        self._load_map(map_data)
        self.allowed_supply_centers = allowed_supply_centers
        self.armies = armies
        self.fleets = fleets
        self.multi_coasts_positions = multi_coasts_positions
        self.phase_type = phase_type
        self.troops = player_troops
        self.territories = player_territories
        # self.overcome_supply_centers = set(self.all_supply_centers) & set(self.territories)
        # self.available_supply_centers = set(self.allowed_supply_centers) & set(self.territories)
        # self.previous_orders = previous_orders
        # self.__convoy_maps = {}
        # self._convoy_routes = defaultdict(lambda: list())
        # self._convoy_routes_stacks = []

    def _load_map(self, data):
        self.seas = data['seas']
        self.all_supply_centers = data['supply_centers']
        self.home_centers = data['home_centers']
        self.centers_to_win = data['scs_to_win']
        # debug
        self.territory_names = data['names']

    def _preprocess(self, ctx):
        proc = PreProcessor()
        failed_orders = proc.process(self.phase_type, ctx.orders)
        for country, territory in failed_orders:
            ctx.orders[country][territory]['failed'] = True

    def _adjudicate(self, ctx):
        judge = Judge(ctx.orders)
        judge.process()
        succeeded, dislodged = [], defaultdict(list)
        for order in judge.orders.list:
            if order.succeeded:
                succeeded.append((order.country, order.id))
            elif order.dislodged_unit:
                dislodged[order.country].append(order.id)
        ctx.succeeded = succeeded
        ctx.dislodged = dislodged

    def _update_positions(self, ctx):
        ctx.new_positions = {}
        ctx.coasts_positions = {territory: position for territory, position in self.multi_coasts_positions.items()}
        for country, troops in self.troops.items():
            ctx.new_positions[country] = {}
            for troop_type, troop_list in troops.items():
                ctx.new_positions[country][troop_type] = list(troop_list)
        for country, src, dst, coast in ctx.movements:
            if src in self.troops[country]['fleets']:
                troop_type = 'fleets'
                if coast is not None:
                    ctx.coasts_positions[dst] = coast
            ctx.new_positions[country][troop_type].remove(src)
            ctx.new_positions[country][troop_type].append(dst)
        fleets = []
        for country, troops in ctx.new_positions.items():
            fleets += troops['fleets']
        for fleet in set(ctx.coasts_positions.keys()) - set(fleets):
            del ctx.coasts_positions[fleet]

    @pipelines.register(PHASES.DIPLOMACY)
    def process_diplomacy(self, orders):
        return ProcessingPipeline(
            self._preprocess,
            self._adjudicate,
            # self._dislodge_troops,
            self._update_positions,
            self._choose_next_phase,
            self._build_next_phase).process(orders)

    def process(self, orders):
        return self.pipelines.call(self.phase_type, self, orders)
