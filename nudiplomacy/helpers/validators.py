from weppy import session
from weppy.validators import inSet


class UserAvatarSet(inSet):
    def __init__(self, theset, labels=None, error_message='Value not allowed',
                 multiple=False, zero='', sort=False):
        self.multiple = multiple
        self._theset = theset
        self.labels = labels
        self.error_message = error_message
        self.zero = zero
        self.sort = sort

    @property
    def theset(self):
        temp = list(self._theset)
        if session.auth:
            if not session.auth.user.facebook:
                temp.remove('facebook')
        return temp
