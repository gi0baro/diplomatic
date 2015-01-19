from weppy.dal import Field, Model, AuthModel, after_insert


class User(AuthModel):
    @after_insert
    def insert_udata(self, fields, oid):
        self.db.UserData.insert(user=oid)


class UserData(Model):
    tablename = "userdata"

    fields = [
        Field("user", "reference auth_user"),
        Field("points", "integer", default=100)
    ]
