from datetime import timedelta

from emmett import abort, now, response

# from diplomatic import app, auth, db, Map
# from diplomatic.handlers import AppStatus
# from diplomatic.contexts import BaseContext
from .. import Game, Map, StatsCountries, StatsGames, StatsTime, app, cache, db
from ..helpers.maps import preview_svg as build_preview, thumb_svg as build_thumb
from ..helpers.stats import avg_turns, country_outcomes, win_rates
from . import front


maps = front.module(__name__, "maps", url_prefix="maps", template_folder="maps")

#: the SVG documents are public and immutable (a new revision is a new row,
#: hence a new URL), so they live outside `front`: no session cookie on a
#: response any shared cache may store, no auth, no app status check
map_files = app.module(__name__, "map_files", url_prefix="maps")
map_files.pipeline = [db.pipe]


STATS_DAYS = 30
CHART_WIDTH, CHART_HEIGHT, BAR_HEIGHT, ZERO_BAR_HEIGHT = 300, 60, 56, 1


def variant_values(variant, countries, games):
    turns = games["turns"] if games else {}
    return {
        "players": len(variant.countries),
        "played": sum(turns.values()),
        "avg_turns": avg_turns(turns),
        "win_rates": [
            (name, colour, f"{rate:.0f}%" if rate is not None else "—")
            for name, colour, rate in win_rates(countries, variant.countries)
        ],
    }


@maps.route("/")
def index():
    variants = Map.all_latest().select(Map.id, Map.name, Map.countries, Map.min_players, orderby=Map.name)
    countries = {row.variant: row for row in StatsCountries.all().select()}
    games = {row.variant: row for row in StatsGames.all().select()}
    rows = {
        variant.id: variant_values(variant, countries.get(variant.name), games.get(variant.name))
        for variant in variants
    }
    return {"maps": variants, "rows": rows}


@maps.route("/<int:mid>")
def detail(mid):
    row = Map.get(mid)
    if not row:
        abort(404)
    countries = StatsCountries.where(lambda m: m.variant == row.name).select().first()
    games = StatsGames.where(lambda m: m.variant == row.name).select().first()
    today = now().date()
    first_day = today - timedelta(days=STATS_DAYS)
    times = StatsTime.where(lambda m: (m.variant == row.name) & (m.date >= first_day)).select(
        StatsTime.date, StatsTime.games, orderby=StatsTime.date
    )
    counts = {entry.date: entry.games for entry in times}
    days = [first_day + timedelta(days=i) for i in range(STATS_DAYS)]
    per_day = [(day, counts.get(day, 0)) for day in days]
    per_day_max = max(1, max(count for day, count in per_day))
    bar_width = CHART_WIDTH / STATS_DAYS
    bars = []
    for i, (day, count) in enumerate(per_day):
        height = count / per_day_max * BAR_HEIGHT if count else ZERO_BAR_HEIGHT
        bars.append(
            {
                "x": i * bar_width,
                "y": CHART_HEIGHT - height,
                "width": bar_width - 1,
                "height": height,
                "count": count,
                "title": f"{day} · {count}",
            }
        )
    outcomes = country_outcomes(countries, row.countries)
    values = variant_values(row, countries, games)
    return {
        "map": row,
        **values,
        "statistics": [
            ("Land territories", len(row.names) - len(row.seas) - len(row.neutrals)),
            ("Water territories", len(row.seas)),
            ("Coastal territories", len(row.coasts)),
            ("Supply centers", len(row.supply_centers)),
            ("Supply centers to win", row.scs_to_win),
            ("Min players", row.min_players),
            ("Games played", values["played"]),
            ("Average turns", values["avg_turns"] if values["avg_turns"] is not None else "—"),
        ],
        "outcomes": outcomes,
        "has_outcomes": any(entry[2] for entry in outcomes),
        "by_players": sorted((games.players if games else {}).items(), key=lambda entry: int(entry[0])),
        "by_pot": [
            (Game.PotType(int(key)).label, count)
            for key, count in sorted((games.pot if games else {}).items(), key=lambda entry: int(entry[0]))
        ],
        "bars": bars,
        "per_day_max": per_day_max,
        "first_day": str(days[0]),
        "last_day": str(days[-1]),
    }


def _svg_row(mid, *fields):
    row = Map.where(lambda m: m.id == mid).select(Map.svg, *fields).first()
    if not row or not row.svg:
        abort(404)
    response.content_type = "image/svg+xml"
    response.headers["cache-control"] = "public, max-age=31536000, immutable"
    return row


@map_files.route("/<int:mid>/map.svg")
@cache.response(duration=None)
def map_svg(mid):
    return _svg_row(mid).svg


@map_files.route("/<int:mid>/preview.svg")
@cache.response(duration=None)
def preview_svg(mid):
    return build_preview(_svg_row(mid, Map.names, Map.countries, Map.init))


@map_files.route("/<int:mid>/thumb.svg")
@cache.response(duration=None)
def thumb_svg(mid):
    return build_thumb(_svg_row(mid, Map.names, Map.countries, Map.init))


# @maps.route()
# @requires(auth.is_logged_in, url("main.index"))
# def new():
#     return dict(form=Map.form())


# @maps.route()
# @requires(auth.is_logged_in, url("main.index"))
# def newffile():
#     fields = {
#         'image': Field("upload"),
#         'data': Field("json")
#     }
#     form = Form(fields)
#     if form.accepted:
#         jdata = form.params.data
#         db.Map.insert(
#             image=db.Map.image.store(form.params.image.file, form.params.image.filename),
#             image_blob=form.params.image.file.read(),
#             **jdata)
#     return dict(form=form)


# @maps.route("/edit/<int:mid>", template="new.haml")
# def edit(mid):
#     record = Map.get(mid)
#     if not record:
#         abort(404)
#     return dict(form=Map.form(record))
