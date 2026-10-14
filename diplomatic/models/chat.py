from emmett import T
from emmett.orm import Field, after_insert, belongs_to, has_many, refers_to, rowmethod, scope

from ..helpers.choice import Choice
from ..helpers.events import publish
from . import TSModel, UUIDModel


class ChatRoom(TSModel, UUIDModel):
    belongs_to("game")
    has_many({"members": "ChatMember.room"}, {"messages": "ChatMessage.room"}, {"readings": "ChatReading.room"})

    class Type(Choice):
        GENERAL = 0, T("General")
        DM = 10, T("Direct")

    type = Field.int()
    name = Field()

    validation = {"type": {"in": Type.choices()}}

    default_values = {"type": Type.GENERAL, "name": "General"}

    repr_values = {"type": Type.repr()}

    indexes = {"game": True, "type": True}

    @scope("accessible_by_user")
    def filter_accessible(self, user):
        return (
            (ChatMember.room == self.id) & (self.db.GameRole.id == ChatMember.player) & (self.db.GameRole.user == user)
        )


class ChatMember(UUIDModel):
    belongs_to({"room": "ChatRoom"}, {"player": "GameRole"})
    has_many({"sent_messages": "ChatMessage.sender"}, {"readings": "ChatReading.member"})

    indexes = {"uniq_member": {"fields": ["room", "player"], "unique": True}}

    @after_insert
    def initialise_readings(self, fields, rid):
        rid.readings.create(room=fields.room)


class ChatMessage(TSModel, UUIDModel):
    belongs_to({"room": "ChatRoom"})
    refers_to({"sender": "ChatMember"})
    has_many({"readings": "ChatReading"})

    text = Field.text()

    validation = {"text": {"presence": True}}

    indexes = {"room": True, "sender": True}

    @classmethod
    def public_for_game(cls, game_id, page=None):
        #: the game's general room in the public shape (the sender as its country), newest first as
        #: api.chat_messages; page=None: all of it (the snapshot at game end), page=N: the N-th page of 25
        roles = cls.db.GameRole  #: the table (game.py imports this module)
        rows = cls.where(
            lambda m: (m.room == ChatRoom.id) & (ChatRoom.game == game_id) & (ChatRoom.type == ChatRoom.Type.GENERAL)
        ).select(
            cls.id,
            cls.text,
            cls.created_at,
            roles.country,
            left=[ChatMember.table.on(ChatMember.id == cls.sender), roles.on(roles.id == ChatMember.player)],
            orderby=~cls.created_at | ~cls.id,
            paginate=(page, 25) if page is not None else None,
        )
        return [
            {
                "id": row.chat_messages.id,
                "sender": row.game_roles.country,
                "text": row.chat_messages.text,
                "created_at": row.chat_messages.created_at,
            }
            for row in rows
        ]

    @after_insert
    def update_readings(self, fields, rid):
        if fields.sender:
            ChatReading.where(lambda m: (m.room == fields.room) & (m.member == fields.sender)).update(message=rid)

    @rowmethod("publish_on_relevant_channels")
    def _publish_on_channels(self, row, pub_ctx):
        for member in row.room.members.select(ChatMember.player):
            publish(pub_ctx, f"chat:{member.player}:messages", "chat", row)


class ChatReading(TSModel, UUIDModel):
    belongs_to({"room": "ChatRoom"}, {"member": "ChatMember"})
    refers_to({"message": "ChatMessage"})

    indexes = {"uniq_member": {"fields": ["room", "member"], "unique": True}, "message": True}

    @scope("accessible_by_user")
    def filter_accessible(self, user):
        return (
            (self.member == ChatMember.id)
            & (ChatMember.player == self.db.GameRole.id)
            & (self.db.GameRole.user == user)
        )

    @scope("of_game")
    def filter_by_game(self, game):
        return (self.room == ChatRoom.id) & (ChatRoom.game == game)
