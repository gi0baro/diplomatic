from weppy.dal import Field, Model, AuthModel, after_insert


class User(AuthModel):
    fields = [
        Field("avatarsrc"),
        Field("avatarimg", "upload")
    ]

    register_visibility = {
        'username': (True, True)
    }

    @after_insert
    def insert_udata(self, fields, oid):
        self.db.UserData.insert(user=oid)
        self.db.UserSettings.insert(user=oid)


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


class UserSettings(Model):
    tablename = "usersettings"

    fields = [
        Field("user", "reference auth_user"),
        Field("notification", "json", default={'email': True})
    ]
