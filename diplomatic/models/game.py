import random
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from diplomatico.constants import OrderType, Phase, Season, Troop
from emmett import T, now, sdict
from emmett.orm import Field, Model, after_insert, belongs_to, has_many, has_one, refers_to, rowmethod, scope

from .. import app
from ..constants import GAME_FEE, WIN_FEE
from ..diplomacy import process_game
from ..helpers.choice import Choice
from ..helpers.validators import SkipProcessingValidator
from ..helpers.widgets import (
    games_bet,
    games_countries_enabled,
    games_join_time,
    games_map,
    games_phase_time,
    games_players_number,
    games_skip_processing,
)
from . import TSModel
from .chat import ChatRoom
from .user import User


LANGS = {"en": T("English"), "it": T("Italian")}


class Game(TSModel):
    belongs_to("user", "map")
    has_many(
        {"players": "GameRole"}, {"phases": "GamePhase"}, {"orders": {"via": "phases"}}, {"chat_rooms": "ChatRoom"}
    )
    has_one({"active_phase": {"target": "GamePhase", "where": lambda m: m.stage == GamePhase.Stage.OPEN}})

    class Access(Choice):
        FREE = 0, T("Free access")
        PASSWORD = 1, T("Password protected")

    class Assignment(Choice):
        RANDOM = 0, T("Random assignment")
        CHOICE = 1, T("Players choice")

    class PotType(Choice):
        WTA = 0, T("Winner takes all")
        PPSC = 1, T("Points per supply center")

    class Press(Choice):
        ALL = 0, T("Allow all")
        GLOBAL = 1, T("Global chat only")
        NONE = 2, T("Disable in-game messaging")

    class Stage(Choice):
        PREGAME = 0, T("Waiting for players")
        GAME = 1, T("In progress")
        PROCESSING = 2, T("Processing")
        PAUSE = 3, T("Paused")
        CRASH = 4, T("Crashed")
        OVER = 5, T("Over")

    class Start(Choice):
        ASAP = 0, T("As soon as enough players joined the game")
        ON_TIME = 1, T("When the join period expired")

    PROC_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

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

    validation = {
        "lang": {"in": app.config.langs},
        "access": {"in": Access.choices()},
        "countries_assignment": {"in": Assignment.choices()},
        "pot_type": {"in": PotType.choices()},
        "press_type": {"in": Press.choices()},
        "stage": {"in": Stage.choices()},
        "starts_on": {"in": Start.choices()},
        "max_turns": {"gt": 0, "allow": "empty"},
        "target_sc": {"gt": 0, "allow": "empty"},
        "phase_time": {"in": {"range": (10, 60 * 24 * 10)}},
        "join_time": {"in": {"range": (10, 60 * 24 * 10)}},
        "skip_processing": {"allow": "empty", "custom": SkipProcessingValidator()},
        "next_process_at": {"allow": "empty"},
        "countries": {"allow": "empty"},
    }

    default_values = {
        "bet": Decimal(1),
        "pot_type": PotType.WTA,
        "starts_on": Start.ASAP,
        "build_everywhere": False,
        "build_on_start": False,
        "anonymous": False,
        "press_type": Press.ALL,
        "access": Access.FREE,
        "stage": Stage.PREGAME,
        "phase_time": 60 * 24,
        "join_time": 60 * 24,
        "is_open": True,
        "skip_processing": {},
        "countries": {},
        "processed_at": now,
        "is_ready": False,
    }

    fields_rw = {
        "user": False,
        "is_open": False,
        "is_ready": False,
        "stage": False,
        "processed_at": False,
        "next_process_at": False,
    }

    form_labels = {
        "map": T("Variant"),
        "lang": T("Language"),
        "players_number": T("Players number"),
        "bet": T("Bet amount"),
        "pot_type": T("Pot type"),
        "phase_time": T("Turn duration"),
        "join_time": T("Join period duration"),
        "starts_on": T("Game start strategy"),
        "build_everywhere": T("Allow builds on all centers"),
        "build_on_start": T("Starts game with a build turn"),
        "anonymous": T("Anonymous players"),
        "press_type": T("In-game messaging"),
        "access": T("Access policy"),
        "max_turns": T("Maximum turns"),
        "target_sc": T("Target supply centers number for win"),
        "skip_processing": T("Avoid game processing on dates"),
        "countries": T("Enabled countries"),
        "countries_assignment": T("Countries assignment policy"),
    }

    form_info = {
        "max_turns": T("Limit number of turns can be played."),
        "countries": T(
            "Select which countries will be available for assignment or could be picked by players. "
            "Remind that, in case you picked the maximum number of players for the variant, this option "
            "won't have effect, and all countries will be available."
        ),
    }

    form_widgets = {
        "map": games_map,
        "players_number": games_players_number,
        "bet": games_bet,
        "countries": games_countries_enabled,
        "phase_time": games_phase_time,
        "join_time": games_join_time,
        "skip_processing": games_skip_processing,
    }

    repr_values = {
        "lang": lambda value: LANGS[value],
        "access": Access.repr(),
        "countries_assignment": Assignment.repr(),
        "pot_type": PotType.repr(),
        "press_type": Press.repr(),
        "stage": Stage.repr(),
        "starts_on": Start.repr(),
    }

    indexes = {"stage": True, "is_open": True}

    @scope("in_stage")
    def filter_stage(self, stage):
        return self.stage == stage

    @after_insert
    def create_general_chatroom(self, fields, rid):
        if fields.press_type != self.Press.NONE:
            rid.chat_rooms.create(game=rid)

    @rowmethod("available_countries")
    def available_countries(self, row):
        enabled_countries = {country for country in row.countries.keys() if row.countries[country]}
        joined_countries = set(row.players(GameRole.country).column("country"))
        return list(enabled_countries - joined_countries)

    def _add_player_to_dm_chat_rooms(self, game, player):
        for other_player in game.players.where(lambda m: m.id != player.id).select():
            room = game.chat_rooms.create(name=f"{other_player.country} - {player.id.country}", type=ChatRoom.Type.DM)
            room.id.members.create(player=player.id)
            room.id.members.create(player=other_player.id)

    @rowmethod("add_player")
    def add_player(self, row, user, country=None):
        available_countries = row.available_countries()
        if not country or (country not in available_countries):
            random.shuffle(available_countries)
            country = next(iter(available_countries), None)
        player = row.players.create(user=user.id, country=country)
        if player.id:
            #: take coins from player
            user.vault().transactions.create(value=-row.bet, description="Bet for game {}".format(row.name))
            if row.press_type != self.Press.NONE:
                #: add player to general chat room
                room = row.chat_rooms.where(lambda m: m.type == ChatRoom.Type.GENERAL).select(limitby=(0, 1)).first()
                room.members.create(player=player.id)
                if row.press_type == self.Press.ALL:
                    self._add_player_to_dm_chat_rooms(row, player)
        return player.id

    @rowmethod("player")
    def get_user(self, row, user):
        return row.players.where(lambda p: p.user == user.id).select().first()

    @rowmethod("player_country")
    def get_user_country(self, row, user):
        player = row.player(user)
        return player.country if player else None

    @rowmethod("player_orders")
    def get_user_orders(self, row, user):
        player = row.player(user)
        if not player:
            return []
        active_phase = row.active_phase()
        if not active_phase:
            return []
        return active_phase.orders.where(lambda m: m.game_role == player.id).select()

    @rowmethod("cancel")
    def cancel_game(self, game):
        for row in game.players.join("user").switch(User).join("vault").select():
            row.vaults.transactions.create(value=row.bet, description="Bet cashback for game {}".format(row.name))
        row.delete_record()

    @rowmethod("start")
    def start_game(self, game):
        players = game.players()
        #: build game phase
        phase_data = {
            "territories": {country: game.map.init["territories"][country] for country in players.column("country")},
            "coasts": game.map.init["coasts"],
        }
        if game.build_on_start:
            phase_data.update(
                year=game.map.year - 1,
                type=GamePhase.Type.BUILDS,
                season=GamePhase.Season.AUTUMN,
                troops={country: {"armies": [], "fleets": []} for country in players.column("country")},
            )
            orders_builder = self._prepare_build_orders_for_start
        else:
            phase_data.update(
                year=game.map.year,
                type=GamePhase.Type.DIPLOMACY,
                season=GamePhase.Season.SPRING,
                troops={country: game.map.init["troops"][country] for country in players.column("country")},
            )
            orders_builder = self._prepare_hold_orders_for_start
        phase = game.phases.create(**phase_data).id
        #: build orders
        for player in game.players():
            for order in orders_builder(game, player.country):
                phase.orders.create(game_role=player.id, **order)
            player.update_record(is_active=True, supply_centers_owned=len(game.map.home_centers[player.country]))
        #: TODO chats
        #: next process cycle
        game.update_record(
            stage=self.Stage.GAME, next_process_at=now() + timedelta(minutes=game.phase_time), is_ready=False
        )

    @rowmethod("process")
    def process_game(self, game):
        #: lock game
        game.update_record(stage=self.Stage.PROCESSING)
        self.db.commit()
        try:
            with self.db.atomic():
                #: launch adjudicator
                outcome, updated_orders, new_orders, successful_orders = process_game(game)
                #: update current phase
                current_phase = game.active_phase()
                current_phase.update_orders_stage_from_processor(updated_orders, successful_orders)
                current_phase.update_record(stage=GamePhase.Stage.CLOSED)
                #: check end
                if outcome.winner:
                    winner = game.players.where(lambda p: p.country == outcome.winner).select().first()
                    game.end(winner, outcome.territories)
                    return
                #: create new phase
                res = game.phases.create(
                    parent=current_phase.id,
                    year=outcome.year,
                    season=outcome.season,
                    type=outcome.phase,
                    territories=outcome.territories,
                    troops=outcome.positions,
                    coasts=outcome.coast_positions,
                    dislodged=outcome.dislodged,
                )
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
                    game.players.where(lambda p: p.id.belongs(active_players)).update(is_active=True, is_ready=False)
                if inactive_players:
                    game.players.where(lambda p: p.id.belongs(inactive_players)).update(is_active=False, is_ready=True)

        except Exception:
            game.update_record(stage=self.Stage.CRASH)
            self.db.commit()
            app.log.exception("OUCH")
            return
        #: update game
        game.update_record(
            stage=self.Stage.GAME, next_process_at=now() + timedelta(minutes=game.phase_time), is_ready=False
        )
        self.db.commit()

    @rowmethod("end")
    def end_game(self, game, winner, territories):
        game.update_record(stage=self.Stage.OVER)
        #: give coins to player(s)
        total_pot = (game.bet * game.players_number - GAME_FEE * game.players_number) * (1 - WIN_FEE)
        if game.pot_type == self.PotType.WTA:
            winner.user.vault().transactions.create(value=total_pot, description="Win for game {}".format(game.name))
            return
        supply_centers = set(game.map.supply_centers)
        all_supply_centers = len(supply_centers)
        for player in game.players():
            player_supply_centers = len(territories.get(player.country, []))
            value = total_pot / all_supply_centers * player_supply_centers
            player.user.vault().transactions.create(value=value, description="Win for game {}".format(game.name))

    @rowmethod("timer")
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
        for army_type in ["armies", "fleets"]:
            for territory in row.map.init["troops"][country][army_type]:
                rv.append({"territory": territory, "type": Order.Type.HOLD})
        return rv

    def _prepare_build_orders_for_start(self, row, country):
        rv = []
        for territory in row.map.init["troops"][country]["armies"]:
            rv.append({"territory": territory, "type": Order.Type.BUILD, "data": {"troop": Troop.ARMY}})
        for territory in row.map.init["troops"][country]["fleets"]:
            order = {"territory": territory, "type": Order.Type.BUILD, "data": {"troop": Troop.FLEET}}
            coast_position = row.map.init["coasts"].get(territory)
            if coast_position:
                order["data"]["coast"] = coast_position
            rv.append(order)
        return rv


class GameRole(Model):
    belongs_to("game", "user")
    has_many("orders", {"chat_memberships": "ChatMember.player"})

    # TODO: add stage with relevant values, eg: participating, defeated, won..
    country = Field(notnull=True)
    is_active = Field(notnull=True)
    is_ready = Field.bool(notnull=True)
    # stage = Field.int(notnull=True)
    supply_centers_owned = Field.int(notnull=True)

    default_values = {"is_active": False, "is_ready": False, "supply_centers_owned": 0}

    fields_rw = {"is_active": (True, False), "supply_centers_owned": False}

    indexes = {
        "uniq_role": {"fields": ["game", "user", "country"], "unique": True},
        "is_active": True,
        "is_ready": True,
    }


class GamePhase(TSModel):
    belongs_to("game")
    refers_to({"parent": "self"})
    has_many("orders")

    Season = Season
    Type = Phase

    class Stage(Choice):
        OPEN = 0, T("Open")
        READY = 1, T("Ready")
        CLOSED = 2, T("Closed")

    year = Field.int(notnull=True)
    season = Field.int(notnull=True)
    type = Field.int(notnull=True)
    stage = Field.int(notnull=True)
    territories = Field.json(notnull=True)
    troops = Field.json(notnull=True)
    coasts = Field.json(notnull=True)
    dislodged = Field.json(notnull=True)

    validation = {
        "season": {"in": list(Season)},
        "stage": {"in": Stage.choices()},
        "type": {"in": list(Type)},
        "coasts": {"presence": False},
        "dislodged": {"presence": False},
    }

    default_values = {
        "stage": Stage.OPEN,
        "territories": {},
        "troops": {"armies": [], "fleets": []},
        "coasts": {},
        "dislodged": {},
    }

    repr_values = {"stage": Stage.repr()}

    indexes = {
        "game": True,
        "stage": True,
        "unique_phase": {"fields": ["game", "year", "season", "type"], "unique": True},
    }

    @rowmethod("orders_grouped")
    def _orders_grouped(self, phase):
        rv = defaultdict(list)
        orders = phase.orders.join("game_role").select()
        for order in orders:
            rv[order.game_role.country].append(order)
        return rv

    @rowmethod("orders_for_processor")
    def _orders_for_processor(self, phase):
        rv = defaultdict(dict)
        orders = phase.orders.join("game_role").select()
        for order in orders:
            order_data = {"type": order.type}
            order_data.update(**order.data)
            rv[order.game_role.country][order.territory] = order_data
        return rv

    @rowmethod("update_orders_stage_from_processor")
    def _update_orders_from_processor(self, phase, orders, succeeded):
        for territory, data in orders.items():
            phase.orders.where(lambda o: (o.territory == territory) & (o.type != data["type"])).update(**data)
        phase.orders.where(lambda o: o.territory.belongs(succeeded)).update(stage=Order.Stage.SUCCESSFUL)
        phase.orders.where(lambda o: o.stage == Order.Stage.PLANNED).update(stage=Order.Stage.FAILED)


class Order(TSModel):
    belongs_to("game_role", "game_phase")

    Type = OrderType

    class Stage(Choice):
        PLANNED = 0, T("Planned")
        SUCCESSFUL = 1, T("Successful")
        FAILED = 2, T("Failed")

    territory = Field(notnull=True)
    type = Field.int(notnull=True)
    data = Field.json(notnull=True)
    stage = Field.int(notnull=True)

    validation = {
        "type": {"in": list(Type)},
        "stage": {"in": Stage.choices()},
        "data": {"presence": False},
    }

    default_values = {"type": Type.HOLD, "data": {}, "stage": Stage.PLANNED}

    repr_values = {"stage": Stage.repr()}

    indexes = {"uniq_orders": {"fields": ["game_role", "game_phase", "territory"], "unique": True}}

    @scope("in_stage")
    def filter_stage(self, stage):
        return self.stage == stage

    @scope("failed")
    def filter_failed(self):
        return self.stage == self.Stage.FAILED
