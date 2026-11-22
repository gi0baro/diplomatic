from emmett import T, url
from emmett.helpers import get_flashed_messages
from emmett.pipeline import Injector

from . import Notification, app, auth
from .helpers.games import duration


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
    def uservault():
        if not auth.user:
            return None
        return auth.user.vault()

    @staticmethod
    def unread_notifications():
        return Notification.unread_count(auth.user.id)

    @staticmethod
    def flashes():
        return get_flashed_messages(with_categories=True)

    @staticmethod
    def userpic():
        return url("download", auth.user.avatar_img)

    duration = staticmethod(duration)
