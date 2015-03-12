from gravatar import Gravatar
from weppy import Helper, T, url
from nudiplomacy import db, auth, cache


class BaseContext(Helper):
    T = T

    @staticmethod
    def current_user():
        return auth.user

    @staticmethod
    def userdata():
        def _get():
            return db.UserData(user=auth.user.id).as_dict()
        if not auth.user:
            return {}
        return cache.redis("userdata_"+str(auth.user.id), _get)

    @staticmethod
    def userpic():
        if auth.user.avatar_source == "gravatar":
            return Gravatar(auth.user.email).thumb
        elif auth.user.avatar_source == "facebook":
            return "https://graph.facebook.com/" + auth.user.facebook + \
                "/picture?type=normal"
        else:
            return url('download', auth.user.thumbnail)

    @staticmethod
    def pretty_gamephasetime(minutes):
        hours = minutes/60
        m = minutes
        h = 0
        d = hours/24
        if hours != 0:
            if d != 0:
                h = hours % 24
            m = minutes % 60
        rv = ""
        comma = False
        if d:
            rv += str(d)+" day"
            comma = True
        if h:
            s = str(h)+" hours"
            if comma:
                s = " ,"+s
            rv += s
        if m:
            s = str(m)+" minutes"
            if comma:
                s = " ,"+s
            rv += s
        return rv
