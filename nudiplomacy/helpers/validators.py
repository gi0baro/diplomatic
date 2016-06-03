from weppy import session
from weppy.validators import Validator, inSet


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
                temp.remove('facebook')
        return temp
