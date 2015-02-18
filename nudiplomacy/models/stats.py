# -*- coding: utf-8 -*-

from weppy import request
from weppy.dal import Field, Model


class TimeStats(Model):
    tablename = "stats_time"

    fields = [
        Field("map", "reference maps"),
        Field("year", "integer", default=lambda: request.now.year),
        Field("data", "json", default={})
    ]


class GameStats(Model):
    tablename = "stats_games"

    fields = [
        Field("map", "reference maps"),
        Field("lang", "json", default={}),
        Field("nplayers", "json", default={}),
        Field("pot", "json", default={'wta': 0, 'ppsc': 0}),
        Field("turns", "json", default={})
    ]


class CountryStats(Model):
    tablename = "stats_countries"

    fields = [
        Field("map", "reference maps"),
        Field("played", "json", default={}),
        Field("won", "json", default={}),
        Field("survived", "json", default={}),
        Field("defeated", "json", default={}),
        Field("drawn", "json", default={})
    ]
