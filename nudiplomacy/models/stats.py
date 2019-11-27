# -*- coding: utf-8 -*-

from emmett import request
from emmett.dal import Field, Model, belongs_to


class TimeStats(Model):
    tablename = "stats_time"

    belongs_to('map')

    year = Field('int', default=lambda: request.now.year)
    data = Field('json')


class GameStats(Model):
    tablename = "stats_games"

    belongs_to('map')

    lang = Field('json', default={})
    nplayers = Field('json', default={})
    pot = Field('json', default={'wta': 0, 'ppsc': 0})
    turns = Field('json', default={})


class CountryStats(Model):
    tablename = "stats_countries"

    belongs_to('map')

    played = Field('json', default={})
    won = Field('json', default={})
    survived = Field('json', default={})
    defeated = Field('json', default={})
    drawn = Field('json', default={})
