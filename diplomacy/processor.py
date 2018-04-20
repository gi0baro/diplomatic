# -*- coding: utf-8 -*-

from collections import defaultdict
from .checkers import PreProcessor
from .constants import ORDERS, PHASES, SEASONS
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
    order_builders = registry()

    def __init__(
        self, map_data, allowed_supply_centers, phase_type, year, season, troops, territories, multi_coasts_positions,
        previous_orders=[], logger=None
    ):
        self._logger = logger
        self._load_map(map_data)
        self.allowed_supply_centers = allowed_supply_centers
        self.phase_type = phase_type
        self.year = year
        self.season = season
        self.troops = troops
        self.territories = territories
        self.multi_coasts_positions = multi_coasts_positions
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

    def _retreats_default_orders(self, ctx):
        for country, orders in ctx.orders.items():
            for territory, order in orders.items():
                if order['type'] == ORDERS.HOLD:
                    order['type'] = ORDERS.DISBAND

    def _builds_default_orders(self, ctx):
        for country, orders in ctx.orders.items():
            centers = set(self.all_supply_centers) & set(self.territories[country])
            troops = self.troops[country]['armies'] + self.troops[country]['fleets']
            if len(troops) <= len(centers):
                continue
            required_disbands = len(troops) - len(centers)
            disband_orders = []
            other_orders = []
            for territory, order in orders.items():
                if order['type'] == ORDERS.DISBAND:
                    disband_orders.append(territory)
                else:
                    other_orders.append(territory)
            if len(disband_orders) >= required_disbands:
                continue
            diff = required_disbands - len(disband_orders)
            to_disband = other_orders[:diff]
            for territory in to_disband:
                orders[territory] = {'type': ORDERS.DISBAND}

    def _make_movements(self, ctx):
        ctx.movements = []
        for country, orders in ctx.orders.items():
            for territory, order in orders.items():
                if order['type'] == ORDERS.MOVE:
                    ctx.movements.append((country, territory, order['dst'], order.get('coast')))

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

    def _next_phase_from_diplomacy(self, ctx):
        ctx.year = self.year
        ctx.season = self.season
        if ctx.dislodged:
            ctx.phase_type = PHASES.RETREATS
            return
        if self.season == SEASONS.SPRING:
            ctx.phase_type = PHASES.DIPLOMACY
            ctx.season = SEASONS.AUTUMN
        else:
            ctx.phase_type = PHASES.BUILDS

    def _update_territories(self, ctx):
        ctx.territories = {}
        for country, territories in self.territories.items():
            ctx.territories[country] = list(territories)
        seas = set(self.seas)
        supply_centers = set(self.all_supply_centers)
        for country, troop_data in ctx.new_positions.items():
            all_troops = troop_data['armies'] + troop_data['fleet']
            troops_set = set(all_troops) - seas
            if self.season == SEASONS.SPRING:
                troops_set = troops_set - supply_centers
            to_add = troops_set - set(ctx.territories[country])
            for territory in to_add:
                ctx.territories[country].append(territory)
            other_countries = set(ctx.territories.keys()) - {country}
            for other_country in other_countries:
                for territory in set(ctx.territories[other_country]) & to_add:
                    ctx.territories[other_country].remove(territory)

    def _active_countries_from_diplomacy(self, ctx):
        ctx.countries = list(ctx.new_positions.keys())

    def _build_new_orders(self, ctx):
        self.order_builders.call(ctx.phase_type, self, ctx)

    @order_builders.register(PHASES.DIPLOMACY)
    def _build_diplomacy_orders(self, ctx):
        ctx.new_orders = {}
        for country in ctx.countries:
            ctx.new_orders[country] = []
            for troops in ctx.new_positions[country].values():
                ctx.new_orders.append({'type': ORDERS.HOLD})

    @order_builders.register(PHASES.RETREATS)
    def _build_retreats_orders(self, ctx):
        ctx.new_orders = {}
        for country, troops in ctx.dislodged:
            ctx.new_orders[country] = []
            for troop in troops:
                ctx.new_orders.append({'type': ORDERS.DISBAND})

    @order_builders.register(PHASES.BUILDS)
    def _build_builds_orders(self, ctx):
        ctx.new_orders = {}
        for country in ctx.countries:
            ctx.new_orders[country] = []
            centers = set(self.all_supply_centers) & set(ctx.territories[country])
            troops = ctx.new_positions[country]['armies'] + ctx.new_positions[country]['fleets']
            if len(centers) > len(troops):
                allowed_supply_centers = set(self.allowed_supply_centers) & set(ctx.territories[country])
                troops = allowed_supply_centers - set(troops)
            for troop in troops:
                ctx.new_orders[country].append(troop)

    def _check_win(self, ctx):
        winners = []
        for country, territories in ctx.territories.items():
            centers = set(self.all_supply_centers) & set(territories)
            if len(centers) >= self.centers_to_win:
                winners.append((country, len(centers)))
        if not winners:
            return
        winners_count = 0
        high = max(winners, key=lambda el: el[1])
        for country, centers in winners:
            if centers == high[1]:
                winners_count += 1
        if winners_count != 1:
            return
        ctx.end = True
        ctx.winner = high[0]

    @pipelines.register(PHASES.DIPLOMACY)
    def process_diplomacy(self, orders):
        return ProcessingPipeline(
            self._preprocess,
            self._adjudicate,
            self._make_movements,
            self._update_positions,
            self._next_phase_from_diplomacy,
            self._update_territories,
            self._active_countries_from_diplomacy,
            self._build_new_orders,
            self._check_win).process(orders)

    # @pipelines.register(PHASES.RETREATS)
    # def process_retreats(self, orders):
    #     return ProcessingPipeline(
    #         self._preprocess,
    #         self._retreats_default_orders).process(orders)

    # @pipelines.register(PHASES.BUILDS)
    # def process_retreats(self, orders):
    #     return ProcessingPipeline(
    #         self._preprocess,
    #         self._builds_default_orders,
    #         self._build_new_orders).process(orders)

    def process(self, orders):
        return self.pipelines.call(self.phase_type, self, orders)
