from emmett import abort

from .. import Game, GameRole, Map, User, UserStats, cache, db
from . import front, query_page


PAGE_SIZE = 25

RANKING_SIZE = 100
RANKING_TTL = 300

users = front.module(__name__, "users", url_prefix="players", template_folder="users")


@cache(duration=RANKING_TTL)
def top_ranks():
    return UserStats.all().select(
        orderby=~UserStats.score | ~UserStats.points, paginate=(1, RANKING_SIZE), including="user"
    )


@users.route("/")
def ranking():
    return {"ranks": top_ranks()}


@users.route("/<str:username>")
def profile(username):
    user = User.get(username=username)
    if not user:
        abort(404)
    stats = UserStats.get(user=user.id)
    page = query_page()
    offset = (page - 1) * PAGE_SIZE
    roles = db(
        (GameRole.user == user.id) & (GameRole.game == Game.id) & (Game.stage == Game.Stage.OVER) & (Game.map == Map.id)
    ).select(
        GameRole.table.ALL,
        Game.id,
        Game.name,
        Map.id,
        Map.name,
        orderby=~Game.updated_at | ~Game.id,
        limitby=(offset, offset + PAGE_SIZE + 1),
    )
    return {
        "user": user,
        # The shared header binds user to the signed-in user.
        "profile_user": user,
        "stats": stats,
        "roles": roles[:PAGE_SIZE],
        "page": page,
        "has_next": len(roles) > PAGE_SIZE,
        "GameRole": GameRole,
    }
