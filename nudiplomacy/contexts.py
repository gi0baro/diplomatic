from weppy import Helper, T
from nudiplomacy import auth


class BaseContext(Helper):
    T = T

    @staticmethod
    def current_user():
        return auth.user

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
