from weppy import Helper, T
from nudiplomacy import auth


class BaseContext(Helper):
    T = T

    @staticmethod
    def current_user():
        return auth.user
