# -*- coding: utf-8 -*-

from weppy import Handler
from nudiplomacy import app
from nudiplomacy.helpers.system import isAppOnline


def offline(*args, **kwargs):
    return app.render_template("offline.haml")


class AppStatus(Handler):
    def wrap_call(self, func):
        if isAppOnline():
            return func
        return offline
