from emmett import response

from .. import Game, GamePhase, GameRole, Map, User, UserStats, app, auth, cache, db
from ..helpers.games import CARD_FIELDS, GAME_MAP_FIELDS, build_cards
from . import front


HOME_TTL = 300
HOME_RUNNING = 3
HOME_OPEN = 6
RANK_WINDOW = 5


@cache(duration=HOME_TTL)
def home_totals():
    closed = GamePhase.where(lambda p: p.stage == GamePhase.Stage.CLOSED)
    lifetime = (GamePhase.updated_at.epoch() - GamePhase.created_at.epoch()).sum()
    seconds = closed.select(lifetime).first()[lifetime] or 0
    return {
        "players": User.all().count(),
        "running": Game.running(include_pre=True).count(),
        "played": Game.where(lambda g: g.stage == Game.Stage.OVER).count(),
        "turns": closed.count(),
        "hours": int(seconds // 3600),
    }


@cache(duration=HOME_TTL)
def home_running():
    rows = (
        Game.running()
        .where(lambda g: g.map == Map.id)
        .select(*CARD_FIELDS, *GAME_MAP_FIELDS, orderby="<random>", limitby=(0, HOME_RUNNING))
    )
    games = [row.games for row in rows]
    variants = {row.games.id: row.maps for row in rows}
    return games, variants, build_cards(games, variants, None, True)


@cache(duration=HOME_TTL)
def ranking_window(uid):
    stats = UserStats.where(lambda s: s.user == uid).select(UserStats.score, UserStats.points).first()
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
        games, variants, cards = home_running()
        return {
            "totals": home_totals(),
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
    ).select(*CARD_FIELDS, *GAME_MAP_FIELDS, orderby=Game.next_process_at)
    mine = [row.games for row in rows]
    variants = {row.games.id: row.maps for row in rows}
    cards = build_cards(mine, variants, user, True)
    for game in mine:
        card = cards[game.id]
        role = card["role"]
        card["due"] = bool(game.stage == Game.Stage.GAME and role and role.is_active and not role.is_ready)
    ranks, my_rank, rank_start = ranking_window(user.id)
    open_rows = (
        Game.in_stage(Game.Stage.PREGAME)
        .where(lambda g: (g.is_open == True) & (g.map == Map.id))
        .select(*CARD_FIELDS, *GAME_MAP_FIELDS, orderby=~Game.created_at, limitby=(0, HOME_OPEN))
    )
    open_games = [row.games for row in open_rows]
    open_variants = {row.games.id: row.maps for row in open_rows}
    return {
        "mine": mine,
        "variants": variants,
        "cards": cards,
        "ranks": ranks,
        "my_rank": my_rank,
        "rank_start": rank_start,
        "open_games": open_games,
        "open_variants": open_variants,
        "open_cards": build_cards(open_games, open_variants, user),
        "Game": Game,
        "GameRole": GameRole,
    }


@app.route("/download/<str:filename>", methods="get", pipeline=[db.pipe])
def download(filename):
    return response.wrap_dbfile(db, filename)
