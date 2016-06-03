from weppy.dal import Field, Model, belongs_to, after_insert, before_update
from weppy.tools.auth import AuthUser
from nudiplomacy import app
from nudiplomacy.helpers.validators import UserAvatarSet
from nudiplomacy.helpers.images import thumb_on_send


class User(AuthUser):
    username = Field()
    avatar_src = Field()
    avatar_img = Field('upload')
    facebook = Field()

    form_registration_rw = {
        'username': True
    }
    form_profile_rw = {
        'avatar_src': True,
        'avatar_img': True
    }

    validation = {
        'username': {'presence': True},
        'avatar_src': UserAvatarSet(app.config.auth.photo_source, zero=None)
    }

    @after_insert
    def insert_udata(self, fields, rid):
        self.db.UserData.insert(user=rid)
        self.db.UserSettings.insert(user=rid)

    @before_update
    def update_avatar_thumb(self, dbset, fields):
        if fields.get('avatar_img'):
            thumb_on_send(fields, "avatar_img")


class UserData(Model):
    belongs_to('user')

    credits = Field('int', default=100)
    points = Field('int', default=0)
    played = Field('int', default=0)
    won = Field('int', default=0)
    survived = Field('int', default=0)
    defeated = Field('int', default=0)
    drawn = Field('int', default=0)


_default_notif_settings = {
    'email': {
        'processing': True,
        'messages': False
    }
}


class UserSettings(Model):
    belongs_to('user')

    notification = Field('json', default=_default_notif_settings)
