# -*- coding: utf-8 -*-

import json
from emmett import url
from emmett.html import asis, cat, tag
from .. import db


_games_map_js = """
<script type="text/javascript">
    var mapdata = %(mapref)s;
    $(document).ready(function() {
        act.createGame();
        act._gameFormChange();
    });
</script>"""


def games_map(field, value):
    Map = db.Map._model_
    variants = Map.all().select(Map.id, Map.name, Map.countries, Map.min_players, Map.thumb)
    choices = []
    jsref = {}
    for variant in variants:
        choices.append(tag.option(variant['name'], _value=variant['id']))
        jsref[str(variant['id'])] = {
            'countries': list(variant['countries'].keys()),
            'players_number': [variant['min_players'], len(variant['countries'])],
            'thumb': url("main.download", variant['thumb'])}
    script = _games_map_js % dict(mapref=json.dumps(jsref))
    return cat(
        tag.div(
            tag.select(*choices, _id="games_map", _name="map", _class="form-control"), _class="col-md-6"),
        tag.div(
            tag.img(
                _src=url(url("main.download", variants[0]['thumb'])),
                _style="width: 80%; margin-left: 10%",
                _id="games_map_img"),
            _class="col-md-6"),
        asis(script))


def games_players_number(field, value):
    return tag.select(_id="games_players_number", _name="players_number", _class="form-control")


def games_countries_enabled(field, value):
    return tag.div(
        tag.div(_id="games_countries_enabled", _class="col-sm-12"),
        tag.textarea(_id="games_countries_enabled_hide", _name="countries", _style="display: none;")
    )


def games_bet(field, value):
    return cat(
        tag.div(
            tag.input(
                _id="bet_slider", _type="text", data={
                    'slider-min': 5, 'slider-max': 150, 'slider-step': 5, 'slider-value': 10}),
            _class="col-sm-9"),
        tag.textarea(10, _id="bet_slider_hide", _name="bet", _style="display: none;"),
        tag.div(tag.span("10", _id="bet_slider_text"), _class="col-sm-3")
    )


def games_phase_time(field, value):
    return cat(
        tag.div(
            tag.input(
                _id="phase_slider", _type="text", data={
                    'slider-min': 1, 'slider-max': 34, 'slider-step': 1, 'slider-value': 21}),
            _class="col-sm-12"),
        tag.textarea(60 * 24, _id="phase_slider_hide", _name="phase_time", _style="display: none;"),
        tag.div(tag.span("1 day", _id="phase_slider_text"), _class="col-sm-12")
    )


def games_join_time(field, value):
    return cat(
        tag.div(
            tag.input(
                _id="join_slider", _type="text", data={
                    'slider-min': 1, 'slider-max': 34, 'slider-step': 1, 'slider-value': 21}),
            _class="col-sm-12"),
        tag.textarea(60 * 24, _id="join_slider_hide", _name="join_time", _style="display: none;"),
        tag.div(tag.span("1 day", _id="join_slider_text"), _class="col-sm-12")
    )


def games_skip_processing(field, value):
    days = db.Game._model_.PROC_DAYS
    options = []
    for day in days:
        options.append(
            tag.div(
                tag.div(day, _class="col-sm-8"),
                tag.div(
                    tag.input(_class="boolean checkbox daycheck", _type="checkbox", _value=day), _class="col-sm-4"),
                _class="col-sm-4"))
    return tag.div(
        tag.div(*options, _id="games_sp", _class="col-sm-12"),
        tag.textarea({}, _id="games_sp_hide", _name="skip_processing", _style="display: none;")
    )
