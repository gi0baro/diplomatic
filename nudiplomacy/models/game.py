
from weppy import now
from weppy.orm import Model, Field, belongs_to, has_many


class Game(Model):
    belongs_to('user', 'map')
    has_many(
        {'players': 'GameRole'},
        {'phases': 'GamePhase'},
        {'orders': {'via': 'phases'}})

    POT_TYPES = {'wta': 0, 'ppsc': 1}
    PRESS_TYPES = {'all': 0, 'globals': 1, 'none': 2}
    START_MODES = {'asap': 0, 'on_time': 1}
    ASSIGNMENT_MODES = {'random': 0, 'choice': 1}
    ACCESS_MODES = {'free': 0, 'password': 1}

    name = Field()
    lang = Field()
    players_number = Field.int()
    bet = Field.decimal()
    pot_type = Field.int()
    phase_time = Field.int()
    join_time = Field.int()
    starts_on = Field.int()
    build_everywhere = Field.bool()
    build_on_start = Field.bool()
    anonymous = Field.bool()
    press_type = Field.int()
    access = Field.int()
    password = Field()
    max_turns = Field.int()
    target_sc = Field.int()
    skip_processing = Field.json()
    status = Field.int()
    is_active = Field.bool()
    is_open = Field.bool()
    is_ready = Field.bool()
    countries_assignment = Field.int()

    created_at = Field.datetime()
    processed_at = Field.datetime()
    next_process_at = Field.datetime()
    countries = Field.json()


class GameRole(Model):
    belongs_to('game', 'user')
    has_many('orders')

    country = Field()


class GamePhase(Model):
    belongs_to('game')
    has_many('orders')

    SEASONS = {'spring': 0, 'autumn': 1}
    TYPES = {'diplomacy': 0, 'retreats': 1, 'builds': 2}

    year = Field.int()
    season = Field.int()
    type = Field.int()


class Order(Model):
    belongs_to('game_role', 'game_phase')

    TYPES = {
        'hold': 0, 'move': 1, 'support_hold': 2, 'support_move': 3,
        'convoy': 4}
    STAGES = {'planned': 0, 'successful': 1, 'failed': 2}

    territory = Field()
    type = Field.int()
    data = Field.json()
    stage = Field.int()
