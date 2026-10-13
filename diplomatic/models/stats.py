from emmett import T
from emmett.orm import Field

from ..helpers.choice import Choice
from . import TSModel, UUIDModel


class StatsEvent(TSModel, UUIDModel):
    tablename = "stats_events"

    class Kind(Choice):
        GAME_STARTED = 0, T("Game started")
        GAME_ENDED = 1, T("Game ended")

    variant = Field(notnull=True)
    kind = Field.int(notnull=True)
    data = Field.json(notnull=True)

    validation = {"kind": {"in": Kind.choices()}}

    repr_values = {"kind": Kind.repr()}

    indexes = {"variant": True, "kind": True, "created_at": True}


class StatsCountries(TSModel):
    tablename = "stats_countries"

    variant = Field(notnull=True)
    played = Field.json(notnull=True)
    won = Field.json(notnull=True)
    survived = Field.json(notnull=True)
    defeated = Field.json(notnull=True)
    drawn = Field.json(notnull=True)

    validation = {
        "played": {"presence": False},
        "won": {"presence": False},
        "survived": {"presence": False},
        "defeated": {"presence": False},
        "drawn": {"presence": False},
    }

    default_values = {"played": {}, "won": {}, "survived": {}, "defeated": {}, "drawn": {}}

    indexes = {"uniq_variant": {"fields": ["variant"], "unique": True}}


class StatsGames(TSModel):
    tablename = "stats_games"

    variant = Field(notnull=True)
    lang = Field.json(notnull=True)
    players = Field.json(notnull=True)
    pot = Field.json(notnull=True)
    turns = Field.json(notnull=True)

    validation = {
        "lang": {"presence": False},
        "players": {"presence": False},
        "pot": {"presence": False},
        "turns": {"presence": False},
    }

    default_values = {"lang": {}, "players": {}, "pot": {}, "turns": {}}

    indexes = {"uniq_variant": {"fields": ["variant"], "unique": True}}


class StatsTime(TSModel):
    tablename = "stats_time"

    variant = Field(notnull=True)
    date = Field.date(notnull=True)
    games = Field.int(notnull=True)

    default_values = {"games": 0}

    indexes = {"uniq_variant_date": {"fields": ["variant", "date"], "unique": True}}
