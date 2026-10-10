# -*- coding: utf-8 -*-

# from gravatar import Gravatar
from emmett import T, url
from emmett.pipeline import Injector

from . import app, auth
from .helpers.utils import cached_user_stats


class BaseContext(Injector):
    T = T

    @staticmethod
    def debug():
        return app.debug

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
    def userpic():
        # if auth.user.avatar_src == "gravatar":
        #     return Gravatar(auth.user.email).thumb
        # elif auth.user.avatar_src == "facebook":
        #     return "https://graph.facebook.com/" + auth.user.facebook + \
        #         "/picture?type=normal"
        # else:
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
