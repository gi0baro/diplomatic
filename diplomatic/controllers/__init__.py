from emmett import redirect, request, url
from emmett.pipeline import RequirePipe

from .. import app, auth, db, sessions
from ..contexts import BaseContext


auth_routes = auth.module(
    __name__, url_prefix="account", pipeline=[sessions, db.pipe, auth.pipe], injectors=[BaseContext()]
)

front = app.module(__name__, "front")
front.pipeline = [sessions, db.pipe, auth.pipe]
front.injectors = [BaseContext()]

authenticated = front.module(__name__, "auth")
authenticated.pipeline = [RequirePipe(auth.is_logged, url("auth.login"))]


@auth_routes.after_login
def after_login(form):
    redirect(url("front.index"))


@auth_routes.after_registration
def after_registration(form, user, logged_in):
    redirect(url("front.index"))


def query_page():
    try:
        return max(1, int(request.query_params.page or 1))
    except ValueError:
        return 1


from . import _internal, api, games, main, maps, users, ws
