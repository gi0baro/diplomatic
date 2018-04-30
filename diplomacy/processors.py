# -*- coding: utf-8 -*-

from collections import defaultdict
from .checkers import PreProcessor, Validator
from .constants import ORDERS, PHASES, SEASONS, TROOPS
from .helpers import Logger, adict, registry
from .judge import Judge


class OrdersProcessor(Logger):
    def __init__(
        self, map_data, build_everywhere_policy, phase_type, troops, multi_coasts_positions, player_country,
        player_troops, player_territories, previous_orders=[], logger=None
    ):
        super().__init__(logger)
        self.map_data = map_data
        self.build_everywhere = build_everywhere_policy
        self.phase_type = phase_type
        self.player_country = player_country
        self.game_data = self._build_game_data(
            troops, multi_coasts_positions, player_troops, player_territories, previous_orders)

    def _build_game_data(self, troops, multi_coasts_positions, player_troops, player_territories, previous_orders):
        rv = adict(
            allowed_supply_centers=(
                list(self.map_data['supply_centers']) if self.build_everywhere else
                self.map_data['home_centers'][self.player_country]),
            phase_type=self.phase_type,
            armies=[],
            fleets=[],
            multi_coasts_positions=multi_coasts_positions,
            player_troops=player_troops,
            player_territories=player_territories,
            previous_orders=previous_orders
        )
        for country, troops_data in troops.items():
            rv.armies.extend(troops_data['armies'])
            rv.fleets.extend(troops_data['fleets'])
        return rv

    def _validate(self, orders):
        if not orders:
            return orders, 'Empty orders'
        #: validate orders
        error = None
        checker = Validator(
            self.map_data, **self.game_data, logger=self.log)
        invalids = checker.process(orders)
        if invalids:
            error = "Validation failed"
            self.log("[OrderProc] found invalid orders: " + str(invalids))
        #: clean orders from invalid ones
        for fail_id in set(invalids) & set(orders.keys()):
            if self.phase_type in ["diplomacy", "builds"]:
                orders[fail_id] = dict(type="hold")
            elif self.phase_type == "retreats":
                orders[fail_id] = dict(type="disband")
        return orders, error

    def process(self, orders={}):
        return self._validate(orders)


class ProcessingPipeline(object):
    def __init__(self, *methods):
        self.methods = methods

    def process(self, orders):
        ctx = adict(orders=orders)
        for method in self.methods:
            method(ctx)
        return ctx


class GameProcessor(Logger):
    pipelines = registry()
    active_builders = registry()
    order_builders = registry()

    def __init__(
        self, map_data, build_everywhere_policy, phase_type, year, season, troops, territories, multi_coasts_positions,
        logger=None
    ):
        super().__init__(logger)
        self.build_everywhere = build_everywhere_policy
        self._load_map(map_data)
        self.phase_type = phase_type
        self.year = year
        self.season = season
        self.troops = troops
        self.territories = territories
        self.multi_coasts_positions = multi_coasts_positions

    def _load_map(self, data):
        self.seas = data['seas']
        self.all_supply_centers = data['supply_centers']
        if self.build_everywhere:
            self.allowed_supply_centers = list(data['supply_centers'])
        else:
            self.allowed_supply_centers = []
            for country, centers in data['home_centers'].items():
                self.allowed_supply_centers.extend(centers)
        self.centers_to_win = data['scs_to_win']
        # debug
        self.territory_names = data['names']

    def _preprocess(self, ctx):
        proc = PreProcessor(ctx.orders)
        failed_orders = proc.process(self.phase_type)
        for country, territory in failed_orders:
            ctx.orders[country][territory]['failed'] = True

    def _adjudicate(self, ctx):
        orders = {}
        for country, orders in ctx.orders.items():
            for territory, order in orders.items():
                orders[territory] = order
                orders[territory]['country'] = country
                orders[territory]['name'] = self.territory_names[territory]
        judge = Judge(orders)
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

    def _make_movements_or_disbands(self, ctx):
        succeeded = []
        ctx.disbands = defaultdict(list)
        ctx.movements = []
        for country, orders in ctx.orders.items():
            for territory, order in orders.items():
                disband = True
                if order['type'] == ORDERS.RETREAT:
                    if not order.get('failed', False):
                        succeeded.append((country, territory))
                        disband = False
                        ctx.movements.append((country, territory, order['dst'], order.get('coast')))
                else:
                    succeeded.append((country, territory))
                if disband:
                    ctx.disbands[country].append(territory)
        ctx.succeeded = succeeded

    def _make_disbands(self, ctx):
        ctx.disbands = defaultdict(list)
        for country, orders in ctx.orders.items():
            for territory, order in orders.items():
                if order['type'] == ORDERS.DISBAND:
                    ctx.disbands[country].append(territory)

    def _prepare_positions(self, ctx):
        ctx.positions = {}
        for country, troops in self.troops.items():
            ctx.positions[country] = {}
            for troop_type, troop_list in troops.items():
                ctx.positions[country][troop_type] = list(troop_list)
        ctx.coasts_positions = {territory: position for territory, position in self.multi_coasts_positions.items()}

    def _update_positions(self, ctx):
        for country, src, dst, coast in ctx.movements:
            troop_type = 'armies'
            if src in self.troops[country]['fleets']:
                troop_type = 'fleets'
                if coast is not None:
                    ctx.coasts_positions[dst] = coast
            ctx.positions[country][troop_type].remove(src)
            ctx.positions[country][troop_type].append(dst)
        fleets = []
        for country, troops in ctx.positions.items():
            fleets += troops['fleets']
        for fleet in set(ctx.coasts_positions.keys()) - set(fleets):
            del ctx.coasts_positions[fleet]

    def _update_builds(self, ctx):
        builds = []
        for country, orders in ctx.orders.items():
            for territory, order in orders.items():
                if order['type'] == ORDERS.BUILD:
                    builds.append((country, territory, order))
        for country, territory, order in builds:
            if order.get('troop') == TROOPS.ARMY:
                ctx.positions[country]['armies'].append(territory)
                continue
            ctx.positions[country]['fleets'].append(territory)
            coast = order.get('coast')
            if coast is not None:
                ctx.coasts_positions[territory] = coast

    def _update_disbands(self, ctx):
        for country, territories in ctx.disbands:
            for troop_type in ['armies', 'fleets']:
                ctx.positions[country][troop_type] = list(set(ctx.positions[troop_type]) - set(territories))

    def _prepare_territories(self, ctx):
        ctx.territories = {}
        for country, territories in self.territories.items():
            ctx.territories[country] = list(territories)

    def _update_territories(self, ctx):
        seas = set(self.seas)
        supply_centers = set(self.all_supply_centers)
        for country, troop_data in ctx.positions.items():
            all_troops = troop_data['armies'] + troop_data['fleets']
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

    def _next_phase_from_retreats(self, ctx):
        ctx.year = self.year
        ctx.season = self.season
        if self.season == SEASONS.SPRING:
            ctx.phase_type = PHASES.DIPLOMACY
            ctx.season = SEASONS.AUTUMN
        else:
            ctx.phase_type = PHASES.BUILDS

    def _next_phase_from_builds(self, ctx):
        ctx.phase_type = PHASES.DIPLOMACY
        ctx.year = self.year + 1
        ctx.season = SEASONS.SPRING

    def _build_active_countries(self, ctx):
        self.active_builders.call(ctx.phase_type, self, ctx)

    @active_builders.register(PHASES.DIPLOMACY)
    def _active_countries_diplomacy(self, ctx):
        ctx.countries = list(ctx.positions.keys())

    @active_builders.register(PHASES.RETREATS)
    def _active_countries_retreats(self, ctx):
        ctx.countries = list(ctx.dislodged.keys())

    @active_builders.register(PHASES.BUILDS)
    def _active_countries_builds(self, ctx):
        ctx.countries = []
        for country, troops in ctx.positions.items():
            centers = set(self.all_supply_centers) & set(ctx.territories[country])
            if len(troops['armies']) + len(troops['fleets']) != len(centers):
                ctx.countries.append(country)

    def _build_new_orders(self, ctx):
        self.order_builders.call(ctx.phase_type, self, ctx)

    @order_builders.register(PHASES.DIPLOMACY)
    def _build_diplomacy_orders(self, ctx):
        ctx.new_orders = {}
        for country in ctx.countries:
            ctx.new_orders[country] = []
            for troops in ctx.positions[country].values():
                for troop in troops:
                    ctx.new_orders[country].append({'territory': troop, 'type': ORDERS.HOLD})

    @order_builders.register(PHASES.RETREATS)
    def _build_retreats_orders(self, ctx):
        ctx.new_orders = {}
        for country in ctx.countries:
            ctx.new_orders[country] = []
            for troop in ctx.dislodged[country]:
                ctx.new_orders[country].append({'territory': troop, 'type': ORDERS.DISBAND})

    @order_builders.register(PHASES.BUILDS)
    def _build_builds_orders(self, ctx):
        ctx.new_orders = {}
        for country in ctx.countries:
            ctx.new_orders[country] = []
            centers = set(self.all_supply_centers) & set(ctx.territories[country])
            troops = ctx.positions[country]['armies'] + ctx.positions[country]['fleets']
            if len(centers) > len(troops):
                allowed_supply_centers = set(self.allowed_supply_centers) & set(ctx.territories[country])
                troops = allowed_supply_centers - set(troops)
            for troop in troops:
                ctx.new_orders[country].append({'territory': troop, 'type': ORDERS.HOLD})

    def _check_win(self, ctx):
        if ctx.phase_type != PHASES.BUILDS:
            return
        self._win_compute(ctx)

    def _win_compute(self, ctx):
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
            self._prepare_positions,
            self._update_positions,
            self._next_phase_from_diplomacy,
            self._prepare_territories,
            self._update_territories,
            self._build_active_countries,
            self._build_new_orders,
            self._check_win
        ).process(orders)

    @pipelines.register(PHASES.RETREATS)
    def process_retreats(self, orders):
        return ProcessingPipeline(
            self._preprocess,
            self._retreats_default_orders,
            self._prepare_positions,
            self._make_movements_or_disbands,
            self._update_disbands,
            self._update_positions,
            self._next_phase_from_retreats,
            self._prepare_territories,
            self._build_active_countries,
            self._build_new_orders,
            self._check_win
        ).process(orders)

    @pipelines.register(PHASES.BUILDS)
    def process_builds(self, orders):
        return ProcessingPipeline(
            self._preprocess,
            self._builds_default_orders,
            self._prepare_positions,
            self._prepare_territories,
            self._update_builds,
            self._make_disbands,
            self._update_disbands,
            self._next_phase_from_builds,
            self._build_active_countries,
            self._build_new_orders
        ).process(orders)

    def process(self, orders):
        return self.pipelines.call(self.phase_type, self, orders)
