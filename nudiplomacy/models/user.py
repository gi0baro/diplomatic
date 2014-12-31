from weppy import Field
from weppy.dal.models import AuthModel, Model


class User(AuthModel):
    pass


class UserData(Model):
    tablename = "userdata"

    fields = [
        Field("user", "reference auth_user"),
        Field("points", "integer", default=100)
    ]
