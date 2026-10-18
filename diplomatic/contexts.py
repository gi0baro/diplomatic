from emmett import T, url
from emmett.helpers import get_flashed_messages
from emmett.pipeline import Injector

from . import app, auth
from .helpers.utils import cached_user_stats


class BaseContext(Injector):
    T = T

    @staticmethod
    def debug():
        return app.debug

    @staticmethod
    def build_commit():
        return app.config.build_commit

    @staticmethod
    def current_user():
        return auth.user

    @staticmethod
    def userdata():
        if not auth.user:
            return None
        return cached_user_stats(auth.user)

    @staticmethod
    def uservault():
        if not auth.user:
            return None
        return auth.user.vault()

    @staticmethod
    def flashes():
        return get_flashed_messages(with_categories=True)

    @staticmethod
    def userpic():
        return url("download", auth.user.avatar_img)

    @staticmethod
    def pretty_gamephasetime(minutes):
        hours = minutes // 60
        m = minutes
        h = 0
        d = hours // 24
        if hours != 0:
            if d != 0:
                h = hours % 24
            m = minutes % 60
        rv = ""
        comma = False
        if d:
            rv += str(d) + " day"
            comma = True
        if h:
            s = str(h) + " hours"
            if comma:
                s = " ," + s
            rv += s
        if m:
            s = str(m) + " minutes"
            if comma:
                s = " ," + s
            rv += s
        return rv
