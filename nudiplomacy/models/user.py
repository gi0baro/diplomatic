from weppy.dal import Field, Model, AuthModel


class User(AuthModel):
    pass


class UserData(Model):
    tablename = "userdata"

    fields = [
        Field("user", "reference auth_user"),
        Field("points", "integer", default=100)
    ]
