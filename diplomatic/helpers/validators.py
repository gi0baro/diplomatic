# -*- coding: utf-8 -*-

from emmett import session
from emmett.validators import Validator, inSet

from .. import db


class UserAvatarSet(inSet):
    def __init__(self, theset, labels=None, multiple=False, zero=None, sort=False, message=None):
        Validator.__init__(self, message)
        self.multiple = multiple
        self._theset = theset
        self.labels = labels
        self.zero = zero
        self.sort = sort

    @property
    def theset(self):
        temp = list(self._theset)
        if session.auth:
            if not session.auth.user.facebook:
                temp.remove("facebook")
        return temp


class SkipProcessingValidator(Validator):
    def __call__(self, value):
        input_keys = [key for key in value.keys() if value[key]]
        rv, error = {}, False
        for key in set(input_keys) & set(db.Game._model_.PROC_DAYS):
            rv[key] = True
        if not (0 <= len(rv.keys()) < 7):
            error = "Number of days to skip processing should be between 0 and 6"
        return rv, error
