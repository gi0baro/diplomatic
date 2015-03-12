from weppy.dal import Field, Model, AuthModel, after_insert, before_update
from nudiplomacy import app
from nudiplomacy.helpers.validators import UserAvatarSet
from nudiplomacy.helpers.images import thumb_on_send


class User(AuthModel):
    fields = [
        Field("avatarsrc", default="gravatar"),
        Field("avatarimg", "upload"),
        Field("facebook")
    ]

    register_visibility = {
        'username': (True, True)
    }
    profile_visibility = {
        'avatarsrc': (True, True)
    }

    validators = {
        'avatarsrc': UserAvatarSet(app.config.auth.photo_source, zero=None),
    }

    @after_insert
    def insert_udata(self, fields, oid):
        self.db.UserData.insert(user=oid)
        self.db.UserSettings.insert(user=oid)

    @before_update
    def update_avatar_thumb(self, s, fields):
        if fields.get('avatarimg'):
            thumb_on_send(fields, "avatarimg")


class UserData(Model):
    tablename = "userdata"

    fields = [
        Field("user", "reference auth_user"),
        Field("credits", "integer", default=100),
        Field("points", "integer", default=0),
        Field("played", "integer", default=0),
        Field("won", "integer", default=0),
        Field("survived", "integer", default=0),
        Field("defeated", "integer", default=0),
        Field("drawn", "integer", default=0)
    ]


_default_notif_settings = {
    'email': {
        'processing': True,
        'messages': False
    }
}


class UserSettings(Model):
    tablename = "usersettings"

    fields = [
        Field("user", "reference auth_user"),
        Field("notification", "json", default=_default_notif_settings)
    ]
