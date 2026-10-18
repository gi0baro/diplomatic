from emmett.orm import Field, after_insert, belongs_to, has_many, has_one
from emmett.tools.auth.models import AuthUserBasic

from . import TSModel
from .economy import Vault


class User(AuthUserBasic):
    has_one("vault", {"stats": "UserStats"})
    has_many(
        {"owned_games": "Game"},
        {"participated_games": "GameRole"},
        {"transactions": {"via": "vault"}},
        {"orders": {"via": "participated_games"}},
    )

    username = Field(notnull=True)
    avatar_img = Field.upload()

    form_registration_rw = {"username": True}
    form_profile_rw = {"avatar_img": True}
    form_labels = {"avatar_img": "Avatar"}

    validation = {
        "username": {
            "presence": True,
            "len": {"range": (3, 33)},
            "match": r"^[A-Za-z0-9_.-]+$",
            "unique": True,
            "message": "Username not available",
        }
    }

    indexes = {"email": True, "uniq_username": {"fields": ["username"], "unique": True}}

    @after_insert
    def create_account_data(self, fields, rid):
        UserStats.create(user=rid)
        Vault.create(user=rid)


class UserStats(TSModel):
    tablename = "user_stats"

    belongs_to("user")

    points = Field.int(notnull=True)
    score = Field.int(notnull=True)
    played = Field.int(notnull=True)
    won = Field.int(notnull=True)
    survived = Field.int(notnull=True)
    defeated = Field.int(notnull=True)
    drawn = Field.int(notnull=True)

    default_values = {"points": 0, "score": 0, "played": 0, "won": 0, "survived": 0, "defeated": 0, "drawn": 0}


# _default_notif_settings = {
#     'email': {
#         'processing': True,
#         'messages': False
#     }
# }


# class UserSettings(Model):
#     belongs_to('user')

#     notification = Field('json', default=_default_notif_settings)
