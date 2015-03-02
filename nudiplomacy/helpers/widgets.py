import json
from weppy import tag, cat, asis, url


_games_map_js = """<script type="text/javascript">
    var mapdata = %(mapref)s;
    $(document).ready(function() {
        act.createGame();
        act._gameFormChange();
    });
</script>"""


def games_map(field, value):
    db = field._db
    maps = db(db.Map.id > 0).select(
        db.Map.id, db.Map.name, db.Map.countries, db.Map.minplayers,
        db.Map.thumb
    ).as_list()
    choices = []
    jsref = {}
    for el in maps:
        choices.append(tag.option(el['name'], _value=el['id']))
        jsref[str(el['id'])] = {
            'countries': el['countries'].keys(),
            'nplayers': [el['minplayers'], len(el['countries'])],
            'thumb': url("main.download", el['thumb'])
        }
    script = _games_map_js % dict(mapref=json.dumps(jsref))
    return cat(
        tag.div(
            tag.select(*choices, _id="games_map", _name="map",
                       _class="form-control"),
            _class="col-md-6"),
        tag.div(
            tag.img(
                _src=url(url("main.download", maps[0]['thumb'])),
                _style="width: 80%; margin-left: 10%",
                _id="games_map_img"),
            _class="col-md-6"),
        asis(script))


def games_nplayers(field, value):
    return tag.select(_id="games_nplayers", _name="nplayers",
                      _class="form-control")


def games_ce(field, value):
    return tag.div(
        tag.div(_id="games_ce", _class="col-sm-12"),
        tag.textarea(_id="games_ce_hide", _name="countriesenabled",
                     _style="display: none;")
    )


def games_bet(field, value):
    return cat(
        tag.div(
            tag.input(
                _id="bet_slider", _type="text", data={
                    'slider-min': 5, 'slider-max': 150,
                    'slider-step': 5, 'slider-value': 10}
            ), _class="col-sm-9"),
        tag.textarea(10, _id="bet_slider_hide", _name="bet",
                     _style="display: none;"),
        tag.div(tag.span("10", _id="bet_slider_text"), _class="col-sm-3")
    )


def games_phasetime(field, value):
    return cat(
        tag.div(
            tag.input(
                _id="phase_slider", _type="text", data={
                    'slider-min': 1, 'slider-max': 34,
                    'slider-step': 1, 'slider-value': 21}
            ), _class="col-sm-12"),
        tag.textarea(60*24, _id="phase_slider_hide", _name="phasetime",
                     _style="display: none;"),
        tag.div(tag.span("1 day", _id="phase_slider_text"), _class="col-sm-12")
    )


def games_jointime(field, value):
    return cat(
        tag.div(
            tag.input(
                _id="join_slider", _type="text", data={
                    'slider-min': 1, 'slider-max': 34,
                    'slider-step': 1, 'slider-value': 21}
            ), _class="col-sm-12"),
        tag.textarea(60*24, _id="join_slider_hide", _name="jointime",
                     _style="display: none;"),
        tag.div(tag.span("1 day", _id="join_slider_text"), _class="col-sm-12")
    )


def games_skipproc(field, value):
    options = []
    for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
              "Saturday", "Sunday"]:
        options.append(
            tag.div(
                tag.div(d, _class="col-sm-8"),
                tag.div(
                    tag.input(_class="boolean checkbox daycheck",
                              _type="checkbox", _value=d),
                    _class="col-sm-4"
                ),
                _class="col-sm-4"))
    return tag.div(
        tag.div(*options, _id="games_sp", _class="col-sm-12"),
        tag.textarea(_id="games_sp_hide", _name="skipproc",
                     _style="display: none;")
    )
