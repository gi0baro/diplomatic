from emmett import response

from .. import Game, GamePhase, GameRole, Map, User, UserStats, app, auth, cache, db
from . import front
from .games import CARD_FIELDS, LOBBY_MODES, RUNNING_STAGES, build_cards


HOME_TTL = 300
HOME_RUNNING = 3
HOME_OPEN = 6
RANK_WINDOW = 5


def home_totals():
    closed = GamePhase.where(lambda p: p.stage == GamePhase.Stage.CLOSED)
    lifetime = (GamePhase.updated_at.epoch() - GamePhase.created_at.epoch()).sum()
    seconds = closed.select(lifetime).first()[lifetime] or 0
    return {
        "players": User.all().count(),
        "running": Game.where(lambda g: g.stage.belongs(RUNNING_STAGES)).count(),
        "played": Game.where(lambda g: g.stage == Game.Stage.OVER).count(),
        "turns": closed.count(),
        "hours": int(seconds // 3600),
    }


def home_running():
    rows = Game.where(lambda g: g.stage.belongs(RUNNING_STAGES) & (g.map == Map.id)).select(
        *CARD_FIELDS, Map.id, Map.name, orderby="<random>", limitby=(0, HOME_RUNNING)
    )
    games = [row.games for row in rows]
    variants = {row.games.id: row.maps for row in rows}
    return games, variants, build_cards(games, None)


def ranking_window(user):
    stats = UserStats.where(lambda s: s.user == user.id).select(UserStats.score, UserStats.points).first()
    if not stats:
        return [], None, 0
    ahead = UserStats.where(
        lambda s: (s.score > stats.score) | ((s.score == stats.score) & (s.points > stats.points))
    ).count()
    my_rank = ahead + 1
    total = UserStats.all().count()
    start = max(0, min(my_rank - 3, total - RANK_WINDOW))
    ranks = UserStats.all().select(
        orderby=~UserStats.score | ~UserStats.points, limitby=(start, start + RANK_WINDOW), including="user"
    )
    return ranks, my_rank, start


@front.route("/")
def index():
    user = auth.user
    if not user:
        games, variants, cards = cache("home_running", home_running, HOME_TTL)
        return {
            "totals": cache("home_totals", home_totals, HOME_TTL),
            "games": games,
            "variants": variants,
            "cards": cards,
            "Game": Game,
            "GameRole": GameRole,
        }
    rows = Game.where(
        lambda g: (
            (g.id == GameRole.game)
            & (GameRole.user == user.id)
            & (GameRole.state != GameRole.State.LEFT)
            & (g.stage != Game.Stage.OVER)
            & (g.map == Map.id)
        )
    ).select(*CARD_FIELDS, Map.id, Map.name, orderby=Game.next_process_at)
    mine = [row.games for row in rows]
    variants = {row.games.id: row.maps for row in rows}
    cards = build_cards(mine, user)
    for game in mine:
        card = cards[game.id]
        role = card["role"]
        card["due"] = bool(game.stage == Game.Stage.GAME and role and role.is_active and not role.is_ready)
    ranks, my_rank, rank_start = ranking_window(user)
    open_rows = Game.where(lambda g: LOBBY_MODES["open"](g) & (g.map == Map.id)).select(
        *CARD_FIELDS, Map.id, Map.name, orderby=~Game.created_at, limitby=(0, HOME_OPEN)
    )
    open_games = [row.games for row in open_rows]
    return {
        "mine": mine,
        "variants": variants,
        "cards": cards,
        "ranks": ranks,
        "my_rank": my_rank,
        "rank_start": rank_start,
        "open_games": open_games,
        "open_variants": {row.games.id: row.maps for row in open_rows},
        "open_cards": build_cards(open_games, user),
        "Game": Game,
        "GameRole": GameRole,
    }


# @app.route()
# def regcode():
#     def proc_form(form):
#         if not form.params.code:
#             form.errors.code = "You need a code to register"
#             return
#         row = db.SysJoincode(code=form.params.code)
#         if not row:
#             form.errors.code = "Code you provided is not valid"
#             return
#         if not row.active or row.count >= row.limit:
#             form.errors.code = "Code you provided is no longer active"
#             return
#         mdb.sys_actcodes.upd({'id': row.id}, {'$inc': {'count': 1}})

#     form = Form(Field("code"), onvalidation=proc_form)
#     if form.accepted:
#         session.regCode = form.params.code
#         redirect(url("account", "register"))
#     return dict(form=form)


RANKING_SIZE = 100
RANKING_TTL = 300


def top_ranks():
    return UserStats.all().select(
        orderby=~UserStats.score | ~UserStats.points, paginate=(1, RANKING_SIZE), including="user"
    )


@front.route()
def ranking():
    return {"ranks": cache("ranking", top_ranks, RANKING_TTL)}


# @app.route(helpers=[AppStatus(), BaseContext()])
# def stats():
#     active = db(db.Game.active == True).count()
#     completed = db((db.Game.active == False) &
#                    (db.Game.status != "pregame")).count()
#     pvariants = []
#     return locals()


@app.route("/download/<str:filename>", methods="get", pipeline=[db.pipe])
def download(filename):
    return response.wrap_dbfile(db, filename)
