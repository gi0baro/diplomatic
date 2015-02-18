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


class LangStats(Model):
    tablename = "stats_lang"

    fields = [
        Field("map", "reference maps"),
        Field("data", "json", default={})
    ]


class NPlayerStats(Model):
    tablename = "stats_nplayers"

    fields = [
        Field("map", "reference maps"),
        Field("data", "json", default={})
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
