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
    def duration(minutes):
        #: as human() in games/create.haml: "1 day 12 h 30 min", zero parts omitted
        days, hours, rest = minutes // 1440, minutes // 60 % 24, minutes % 60
        parts = []
        if days:
            parts.append(f"{days} day" if days == 1 else f"{days} days")
        if hours:
            parts.append(f"{hours} h")
        if rest:
            parts.append(f"{rest} min")
        return " ".join(parts)
