# -*- coding: utf-8 -*-

import random
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from diplomacy import constants as dip_const
from weppy import now, T, sdict
from weppy.orm import Model, Field, belongs_to, has_one, has_many, scope, rowmethod

from . import TSModel
from .user import User
from .. import app
from ..constants import GAME_FEE, WIN_FEE
from ..helpers.validators import SkipProcessingValidator
from ..helpers.widgets import (
    games_map, games_players_number, games_bet, games_countries_enabled, games_phase_time, games_join_time,
    games_skip_processing)
from ..gameman.process import process_game


class Game(TSModel):
    belongs_to('user', 'map')
    has_many(
        {'players': 'GameRole'},
        {'phases': 'GamePhase'},
        {'orders': {'via': 'phases'}})
    has_one({'active_phase': {'target': 'GamePhase', 'where': lambda m: m.stage == GamePhase.STAGES['open']}})

    ACCESS_MODES = {'free': 0, 'password': 1}
    ASSIGNMENT_MODES = {'random': 0, 'choice': 1}
    POT_TYPES = {'wta': 0, 'ppsc': 1}
    PRESS_TYPES = {'all': 0, 'global': 1, 'none': 2}
    STAGES = {'pregame': 0, 'game': 1, 'processing': 2, 'pause': 3, 'crash': 4, 'over': 5}
    START_MODES = {'asap': 0, 'on_time': 1}
    PROC_DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    name = Field(notnull=True)
    lang = Field(notnull=True)
    players_number = Field.int(notnull=True)
    bet = Field.decimal(18, 6, notnull=True)
    pot_type = Field.int(notnull=True)
    phase_time = Field.int(notnull=True)
    join_time = Field.int(notnull=True)
    starts_on = Field.int(notnull=True)
    build_everywhere = Field.bool(notnull=True)
    build_on_start = Field.bool(notnull=True)
    anonymous = Field.bool(notnull=True)
    press_type = Field.int(notnull=True)
    access = Field.int(notnull=True)
    password = Field()
    max_turns = Field.int()
    target_sc = Field.int()
    skip_processing = Field.json(notnull=True)
    stage = Field.int()
    # is_active = Field.bool()
    is_open = Field.bool(notnull=True)
    is_ready = Field.bool(notnull=True)
    countries_assignment = Field.int()

    processed_at = Field.datetime()
    next_process_at = Field.datetime()
    countries = Field.json(notnull=True)

    #     repr_lang = {'en': T("English"), 'it': T("Italian")}
    # repr_starts_on = {
    #     Game.START_MODES['asap']: T("As soon as enough players joined the game"),
    #     Game.START_MODES['on_time']: T("When the join period expired")}

    validation = {
        'lang': {'in': app.config.langs},
        'access': {'in': [(ACCESS_MODES['free'], T("Free")), (ACCESS_MODES['password'], T("Password protected"))]},
        'countries_assignment': {'in': [
            (ASSIGNMENT_MODES['random'], T("Random assignment")), (ASSIGNMENT_MODES['choice'], T("Players choice"))]},
        'pot_type': {'in': [
            (POT_TYPES['wta'], T("Winner takes all")), (POT_TYPES['ppsc'], T("Points per supply center"))]},
        'press_type': {'in': [
            (PRESS_TYPES['all'], T("Allow all")), (PRESS_TYPES['global'], T("Global chat only")),
            (PRESS_TYPES['none'], T("Disable in-game messaging"))]},
        'stage': {'in': list(STAGES.values())},
        'starts_on': {'in': [
            (START_MODES['asap'], T("As soon as enough players joined the game")),
            (START_MODES['on_time'], T("When the join period expired"))]},
        'max_turns': {'gt': 0, 'allow': 'empty'},
        'target_sc': {'gt': 0, 'allow': 'empty'},
        'phase_time': {'in': {'range': (10, 60 * 24 * 10)}},
        'join_time': {'in': {'range': (10, 60 * 24 * 10)}},
        'skip_processing': {'allow': 'empty', 'custom': SkipProcessingValidator()},
        'countries': {'allow': 'empty'}
    }

    default_values = {
        'bet': Decimal(1),
        'pot_type': POT_TYPES['wta'],
        'starts_on': START_MODES['asap'],
        'build_everywhere': False,
        'build_on_start': False,
        'anonymous': False,
        'press_type': PRESS_TYPES['all'],
        'access': ACCESS_MODES['free'],
        'stage': STAGES['pregame'],
        'phase_time': 60 * 24,
        'join_time': 60 * 24,
        'is_open': True,
        'skip_processing': {},
        'countries': {},
        'processed_at': now,
        'is_ready': False
    }

    fields_rw = {
        'user': False,
        'is_open': False,
        'is_ready': False,
        'stage': False,
        'processed_at': False,
        'next_process_at': False
    }

    form_labels = {
        'map': T("Variant"),
        'lang': T("Language"),
        'players_number': T("Players number"),
        'bet': T("Bet amount"),
        'pot_type': T("Pot type"),
        'phase_time': T("Turn duration"),
        'join_time': T("Join period duration"),
        'starts_on': T("Game start strategy"),
        'build_everywhere': T("Allow builds on all centers"),
        'build_on_start': T("Starts game with a build turn"),
        'anonymous': T("Anonymous players"),
        'press_type': T("In-game messaging"),
        'access': T("Access policy"),
        'max_turns': T("Maximum turns"),
        'target_sc': T("Target supply centers number for win"),
        'skip_processing': T("Avoid game processing on dates"),
        'countries': T("Enabled countries"),
        'countries_assignment': T("Countries assignment policy")
    }

    form_info = {
        'max_turns': T("Limit number of turns can be played."),
        'countries': T(
            "Select which countries will be available for assignment or could be picked by players. "
            "Remind that, in case you picked the maximum number of players for the variant, this option "
            "won't have effect, and all countries will be available."
        )
    }

    form_widgets = {
        'map': games_map,
        'players_number': games_players_number,
        'bet': games_bet,
        'countries': games_countries_enabled,
        'phase_time': games_phase_time,
        'join_time': games_join_time,
        'skip_processing': games_skip_processing
    }

    repr_values = {
        'lang': lambda value: repr_lang[value],
        'pot_type': lambda value: repr_pot_type[value],
        'starts_on': lambda value: repr_starts_on[value],
        'press_type': lambda value: repr_press_type[value],
        'countries_assignment': lambda value: repr_countries_assignment[value],
        'access': lambda value: repr_access[value]
    }

    indexes = {
        'stage': True
    }

    @scope('in_stage')
    def filter_stage(self, stage):
        return self.stage == self.STAGES[stage]

    @rowmethod('available_countries')
    def available_countries(self, row):
        enabled_countries = set([country for country in row.countries.keys() if row.countries[country]])
        joined_countries = set(row.players(GameRole.country).column('country'))
        return list(enabled_countries - joined_countries)

    @rowmethod('add_player')
    def add_player(self, row, user, country=None):
        available_countries = row.available_countries()
        if not country or (country not in available_countries):
            random.shuffle(available_countries)
            country = next(iter(available_countries), None)
        # app.log.debug('add_player', user, country)
        player = row.players.create(user=user.id, country=country)
        # app.log.debug(player)
        #: take coins from player
        if player.id:
            user.vault().transactions.create(value=-row.bet, description="Bet for game {}".format(row.name))
        return player.id

    @rowmethod('player')
    def get_user(self, row, user):
        return row.players.where(lambda p: p.user == user.id).select().first()

    @rowmethod('player_country')
    def get_user_country(self, row, user):
        player = row.player(user)
        return player.country if player else None

    @rowmethod('player_orders')
    def get_user_orders(self, row, user):
        player = row.player(user)
        if not player:
            return []
        active_phase = row.active_phase()
        if not active_phase:
            return []
        return active_phase.orders.where(lambda m: m.game_role == player.id).select()

    @rowmethod('cancel')
    def cancel_game(self, game):
        for row in game.players.join('user').switch(User).join('vault').select():
            row.vaults.transactions.create(value=row.bet, description="Bet cashback for game {}".format(row.name))
        row.delete_record()

    @rowmethod('start')
    def start_game(self, game):
        players = game.players()
        #: build game phase
        phase_data = {
            'territories': {country: game.map.init['territories'][country] for country in players.column('country')},
            'coasts': game.map.init['coasts']}
        if game.build_on_start:
            phase_data.update(
                year=game.map.year - 1, type=GamePhase.TYPES['builds'], season=GamePhase.SEASONS['autumn'],
                troops={country: {'armies': [], 'fleets': []} for country in players.column('country')})
            orders_builder = self._prepare_build_orders_for_start
        else:
            phase_data.update(
                year=game.map.year, type=GamePhase.TYPES['diplomacy'], season=GamePhase.SEASONS['spring'],
                troops={country: game.map.init['troops'][country] for country in players.column('country')})
            orders_builder = self._prepare_hold_orders_for_start
        phase = game.phases.create(**phase_data).id
        #: build orders
        for player in game.players():
            for order in orders_builder(game, player.country):
                phase.orders.create(game_role=player.id, **order)
            player.update_record(
                is_active=True, supply_centers_owned=len(game.map.home_centers[player.country]))
        #: TODO chats
        #: next process cycle
        game.update_record(
            stage=self.STAGES['game'], next_process_at=now() + timedelta(minutes=game.phase_time), is_ready=False)

    @rowmethod('process')
    def process_game(self, game):
        #: lock game
        game.update_record(stage=self.STAGES['processing'])
        self.db.commit()
        try:
            with self.db.atomic():
                #: launch adjudicator
                proc_ctx, updated_orders, new_orders, successful_orders = process_game(game)
                #: update current phase
                current_phase = game.active_phase()
                current_phase.update_orders_stage_from_processor(updated_orders, successful_orders)
                current_phase.update_record(stage=GamePhase.STAGES['closed'])
                #: check end
                if proc_ctx.end:
                    game.end()
                    return
                #: create new phase
                res = game.phases.create(
                    year=proc_ctx.year,
                    season=proc_ctx.season,
                    type=proc_ctx.phase_type,
                    territories=proc_ctx.territories,
                    troops=proc_ctx.positions,
                    coasts=proc_ctx.coasts_positions,
                    dislodged=dict(proc_ctx.dislodged))
                #: create new orders
                players = game.players()
                players_map = {}
                for player in players:
                    players_map[player.country] = player.id
                    # TODO: update owned supply centers
                active_players = []
                for country, orders in new_orders.items():
                    for order in orders:
                        order.update(game_role=players_map[country])
                        res.id.orders.create(**order)
                    active_players.append(players_map[country])
                active_players = set(active_players)
                inactive_players = set(players_map.values()) - active_players
                print(active_players, inactive_players)
                #: clear roles
                # TODO: maybe add editable status?
                if active_players:
                    game.players.where(
                        lambda p: p.id.belongs(active_players)).update(is_active=True, is_ready=False)
                if inactive_players:
                    game.players.where(
                        lambda p: p.id.belongs(inactive_players)).update(is_active=False, is_ready=True)

        except Exception:
            game.update_record(stage=self.STAGES['crash'])
            self.db.commit()
            app.log.exception('OUCH')
            return
        #: update game
        game.update_record(
            stage=self.STAGES['game'], next_process_at=now() + timedelta(minutes=game.phase_time), is_ready=False)
        self.db.commit()

    @rowmethod('end')
    def end_game(self, game):
        # TODO everything game related
        # game.update_record(stage=self.STAGES['end'])
        #: give coins to player(s)
        winner = None  # TODO fetch real one
        total_pot = (game.bet * game.players_number - GAME_FEE * game.players_number) * (1 - WIN_FEE)
        if game.pot_type == self.POT_TYPES['wta']:
            winner.vault().transactions.create(value=total_pot, description="Win for game {}".format(game.name))
        else:
            for player in game.players():
                # TODO fetch scs in some way
                player_supply_centers = 0
                all_supply_centers = 1
                value = total_pot / all_supply_centers * player_supply_centers
                winner.vault().transactions.create(value=value, description="Win for game {}".format(game.name))

    @rowmethod('timer')
    def get_timer(self, game):
        timeleft = 0
        if game.next_process_at:
            timeleft = int((game.next_process_at - now().naive()).total_seconds())
        timerdata = sdict(d=0, h=0, m=0, s=0)
        if timeleft > 0:
            timerdata.d = timeleft // (60 * 60 * 24)
            timerdata.h = (timeleft // (60 * 60)) % 24
            timerdata.m = (timeleft // 60) % 60
            timerdata.s = timeleft % 60
        return timerdata

    def _prepare_hold_orders_for_start(self, row, country):
        rv = []
        for army_type in ['armies', 'fleets']:
            for territory in row.map.init['troops'][country][army_type]:
                rv.append({'territory': territory, 'type': Order.TYPES['hold']})
        return rv

    def _prepare_build_orders_for_start(self, row, country):
        rv = {}
        for territory in row.map.init['troops'][country]['armies']:
            rv.append({'territory': territory, 'type': Order.TYPES['build'], 'data': {'troop': 'army'}})
        for territory in row.map.init['troops'][country]['fleets']:
            order = {'territory': territory, 'type': Order.TYPES['build'], 'data': {'troop': 'fleet'}}
            coast_position = row.map.init['coasts'].get(territory)
            if coast_position:
                order['data']['coast'] = coast_position
            rv.append(order)
        return rv


class GameRole(Model):
    belongs_to('game', 'user')
    has_many('orders')

    # TODO: add stage with relevant values, eg: participating, defeated, won..
    country = Field(notnull=True)
    is_active = Field(notnull=True)
    is_ready = Field.bool(notnull=True)
    # stage = Field.int(notnull=True)
    supply_centers_owned = Field.int(notnull=True)

    default_values = {
        'is_active': False,
        'is_ready': False,
        'supply_centers_owned': 0
    }

    fields_rw = {
        'is_active': (True, False),
        'supply_centers_owned': False
    }

    indexes = {
        'uniq_role': {'fields': ['game', 'user', 'country'], 'unique': True},
        'is_active': True,
        'is_ready': True
    }


class GamePhase(TSModel):
    belongs_to('game')
    has_many('orders')

    SEASONS = {'spring': dip_const.SEASONS.SPRING, 'autumn': dip_const.SEASONS.AUTUMN}
    STAGES = {'open': 0, 'ready': 1, 'closed': 2}
    TYPES = {
        'diplomacy': dip_const.PHASES.DIPLOMACY, 'retreats': dip_const.PHASES.RETREATS,
        'builds': dip_const.PHASES.BUILDS}

    year = Field.int(notnull=True)
    season = Field.int(notnull=True)
    type = Field.int(notnull=True)
    stage = Field.int(notnull=True)
    territories = Field.json(notnull=True)
    troops = Field.json(notnull=True)
    coasts = Field.json(notnull=True)
    dislodged = Field.json(notnull=True)

    validation = {
        'season': {'in': list(SEASONS.values())},
        'stage': {'in': list(STAGES.values())},
        'type': {'in': list(TYPES.values())}
    }

    default_values = {
        'stage': STAGES['open'],
        'territories': {},
        'troops': {'armies': [], 'fleets': []},
        'coasts': {},
        'dislodged': {}
    }

    indexes = {
        'game': True,
        'stage': True,
        'unique_phase': {'fields': ['game', 'year', 'season', 'type'], 'unique': True}
    }

    @rowmethod('orders_for_processor')
    def _orders_for_processor(self, phase):
        rv = defaultdict(dict)
        orders = phase.orders.join('game_role').select()
        for order in orders:
            order_data = {'type': order.type}
            order_data.update(**order.data)
            rv[order.game_role.country][order.territory] = order_data
        return rv

    @rowmethod('update_orders_stage_from_processor')
    def _update_orders_from_processor(self, phase, orders, succeeded):
        for territory, data in orders.items():
            phase.orders.where(lambda o: (o.territory == territory) & (o.type != data['type'])).update(**data)
        phase.orders.where(lambda o: o.territory.belongs(succeeded)).update(stage=Order.STAGES['successful'])
        phase.orders.where(lambda o: o.stage == Order.STAGES['planned']).update(stage=Order.STAGES['failed'])


class Order(TSModel):
    belongs_to('game_role', 'game_phase')

    TYPES = {
        'hold': dip_const.ORDERS.HOLD, 'move': dip_const.ORDERS.MOVE, 'support_hold': dip_const.ORDERS.SUPPORT_HOLD,
        'support_move': dip_const.ORDERS.SUPPORT_MOVE, 'convoy': dip_const.ORDERS.CONVOY,
        'retreat': dip_const.ORDERS.RETREAT, 'build': dip_const.ORDERS.BUILD, 'disband': dip_const.ORDERS.DISBAND}
    STAGES = {'planned': 0, 'successful': 1, 'failed': 2}

    territory = Field(notnull=True)
    type = Field.int(notnull=True)
    data = Field.json(notnull=True)
    stage = Field.int(notnull=True)

    validation = {
        'type': {'in': list(TYPES.values())},
        'stage': {'in': list(STAGES.values())}
    }

    default_values = {
        'type': TYPES['hold'],
        'data': {},
        'stage': STAGES['planned']
    }

    indexes = {
        'uniq_orders': {'fields': ['game_role', 'game_phase', 'territory'], 'unique': True}
    }

    @scope('in_stage')
    def filter_stage(self, stage):
        return self.stage == self.STAGES[stage]

    @scope('failed')
    def filter_failed(self):
        return self.stage == self.STAGES['failed']


repr_lang = {'en': T("English"), 'it': T("Italian")}
repr_pot_type = {Game.POT_TYPES['wta']: T("Winner takes all"), Game.POT_TYPES['ppsc']: T("Points per supply center")}
repr_starts_on = {
    Game.START_MODES['asap']: T("As soon as enough players joined the game"),
    Game.START_MODES['on_time']: T("When the join period expired")}
repr_press_type = {
    Game.PRESS_TYPES['all']: T("Allow all"), Game.PRESS_TYPES['global']: T("Global chat only"),
    Game.PRESS_TYPES['none']: T("Disable in-game messaging")}
repr_countries_assignment = {
    Game.ASSIGNMENT_MODES['random']: T("Random assignment"), Game.ASSIGNMENT_MODES['choice']: T("Players choice")}
repr_access = {
    Game.ACCESS_MODES['free']: T("Free access"), Game.ACCESS_MODES['password']: T("Password protected")}
