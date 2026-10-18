from emmett import abort

from .. import Game, GameRole, Map, User, UserStats, db
from . import front
from .api import query_page


users = front.module(__name__, "users", url_prefix="users", template_folder="users")
PAGE_SIZE = 25


@users.route("/<str:username>", template="profile.haml", methods="get")
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
