from emmett.validators import Validator

from .. import db


class SkipProcessingValidator(Validator):
    def __call__(self, value):
        input_keys = [key for key in value.keys() if value[key]]
        rv, error = {}, False
        for key in set(input_keys) & set(db.Game._model_.PROC_DAYS):
            rv[key] = True
        if not (0 <= len(rv.keys()) < 7):
            error = "Number of days to skip processing should be between 0 and 6"
        return rv, error
