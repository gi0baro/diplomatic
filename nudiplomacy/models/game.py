# -*- coding: utf-8 -*-

import random
from datetime import timedelta
from decimal import Decimal
from weppy import now
from weppy.orm import Model, Field, belongs_to, has_one, has_many, scope, rowmethod
from . import TSModel
from .user import User
from ..constants import GAME_FEE, WIN_FEE


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
    PRESS_TYPES = {'all': 0, 'globals': 1, 'none': 2}
    STAGES = {'pregame': 0, 'game': 1, 'processing': 2, 'pause': 3, 'crash': 4}
    START_MODES = {'asap': 0, 'on_time': 1}

    name = Field(notnull=True)
    lang = Field(notnull=True)
    players_number = Field.int(notnull=True)
    bet = Field.decimal(18, 6, notnull=True)
    pot_type = Field.int(notnull=True)
    phase_time = Field.int(notnull=True)
    join_time = Field.int()
    starts_on = Field.int(notnull=True)
    build_everywhere = Field.bool(notnull=True)
    build_on_start = Field.bool(notnull=True)
    anonymous = Field.bool(notnull=True)
    press_type = Field.int(notnull=True)
    access = Field.int(notnull=True)
    password = Field()
    max_turns = Field.int()
    target_sc = Field.int()
    skip_processing = Field.json()
    stage = Field.int()
    # is_active = Field.bool()
    is_open = Field.bool(notnull=True)
    # is_ready = Field.bool()
    countries_assignment = Field.int()

    processed_at = Field.datetime()
    next_process_at = Field.datetime()
    countries = Field.json()

    validation = {
        'access': {'in': ACCESS_MODES.values()},
        'countries_assignment': {'in': ASSIGNMENT_MODES.values()},
        'pot_type': {'in': POT_TYPES.values()},
        'press_type': {'in': PRESS_TYPES.values()},
        'stage': {'in': STAGES.values()},
        'starts_on': {'in': START_MODES.values()},
        'max_turns': {'gt': 0, 'allow': 'empty'},
        'target_sc': {'gt': 0, 'allow': 'empty'},
        'phase_time': {'in': {'range': (10, 60 * 24 * 10)}},
        'join_time': {'in': {'range': (10, 60 * 24 * 10)}},
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
        'processed_at': now
    }

    fields_rw = {
        'is_open': False,
        'stage': False,
        'processed_at': False,
        'next_process_at': False
    }

    @rowmethod('available_countries')
    def available_countries(self, row):
        enabled_countries = set([country for country in row.countries.keys() if row.countries[country]])
        joined_countries = set(row.players(GameRole.country).column('country'))
        return list(enabled_countries - joined_countries)

    @rowmethod('add_player')
    def add_player(self, row, user, country=None):
        available_countries = row.available_countries()
        if not country or (country not in available_countries):
            country = random.shuffle(available_countries)
        player = row.players.create(country=country)
        #: take coins from player
        if player.id:
            user.vault().add_expense(value=row.bet, description="Bet for game {}".format(row.name))

    @rowmethod('cancel')
    def cancel_game(self, game):
        for row in game.players.join('user').switch(User).join('vault').select():
            row.vaults.add_credit(value=row.bet, description="Bet cashback for game {}".format(row.name))
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
        phase = GamePhase.create(**phase_data).id
        #: build orders
        for player in game.players():
            for order in orders_builder(game, player.country):
                phase.orders.create(game_role=player.id, **order)
        #: TODO chats
        #: next process cycle
        game.update_record(next_process_at=now() + timedelta(minutes=game.phase_time))

    @rowmethod('end')
    def end_game(self, game):
        # TODO everything game related
        #: give coins to player(s)
        winner = None  # TODO fetch real one
        total_pot = (game.bet * game.players_number - GAME_FEE * game.players_number) * (1 - WIN_FEE)
        if game.pot_type == self.POT_TYPES['wta']:
            winner.vault().add_credit(value=total_pot, description="Win for game {}".format(game.name))
        else:
            for player in game.players():
                # TODO fetch scs in some way
                player_supply_centers = 0
                all_supply_centers = 1
                value = total_pot / all_supply_centers * player_supply_centers
                winner.vault().add_credit(value=value, description="Win for game {}".format(game.name))

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

    country = Field(notnull=True)

    indexes = {
        ('game', 'user', 'country'): {'unique': True}
    }


class GamePhase(Model):
    belongs_to('game')
    has_many('orders')

    SEASONS = {'spring': 0, 'autumn': 1}
    STAGES = {'open': 0, 'ready': 1, 'closed': 2}
    TYPES = {'diplomacy': 0, 'retreats': 1, 'builds': 2}

    year = Field.int(notnull=True)
    season = Field.int(notnull=True)
    type = Field.int(notnull=True)
    stage = Field.int(notnull=True)
    territories = Field.json(notnull=True)
    troops = Field.json(notnull=True)
    coasts = Field.json(notnull=True)
    dislodged = Field.json(notnull=True)

    validation = {
        'season': {'in': SEASONS.values()},
        'stage': {'in': STAGES.values()},
        'type': {'in': TYPES.values()}
    }

    default_values = {
        'stage': STAGES['open'],
        'territories': {},
        'troops': {'armies': [], 'fleets': []},
        'coasts': {},
        'dislodged': {}
    }


class Order(Model):
    belongs_to('game_role', 'game_phase')

    TYPES = {
        'hold': 0, 'move': 1, 'support_hold': 2, 'support_move': 3, 'convoy': 4,
        'retreat': 5, 'build': 6, 'disband': 7}
    STAGES = {'planned': 0, 'successful': 1, 'failed': 2}

    territory = Field(notnull=True)
    type = Field.int(notnull=True)
    data = Field.json(notnull=True)
    stage = Field.int(notnull=True)

    validation = {
        'type': {'in': TYPES.values()},
        'stage': {'in': STAGES.values()}
    }

    default_values = {
        'type': TYPES['hold'],
        'data': {},
        'stage': STAGES['planned']
    }

    @scope('with_status')
    def filter_status(self, status):
        return self.status == self.STAGES[status]

    @scope('failed')
    def filter_failed(self):
        return self.filter_status('failed')
