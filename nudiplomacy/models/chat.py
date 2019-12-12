# -*- coding: utf-8 -*-

from emmett.orm import Model, Field, belongs_to, refers_to, has_many, scope, after_insert

from . import TSModel


class ChatRoom(TSModel):
    belongs_to('game')
    has_many(
        {'members': 'ChatMember.room'},
        {'messages': 'ChatMessage.room'},
        {'readings': 'ChatReading.room'}
    )

    TYPES = {'general': 0, 'dm': 10}

    type = Field.int()
    name = Field()

    validation = {
        'type': {'in': list(TYPES.values())}
    }

    default_values = {
        'type': TYPES['general'],
        'name': 'General'
    }

    indexes = {
        'game': True,
        'type': True
    }

    @scope('accessible_by_user')
    def filter_stage(self, user):
        return (
            (ChatMember.room == self.id) &
            (self.db.GameRole.id == ChatMember.player) &
            (self.db.GameRole.user == user))


class ChatMember(Model):
    belongs_to(
        {'room': 'ChatRoom'},
        {'player': 'GameRole'}
    )
    has_many(
        {'sent_messages': 'ChatMessage.sender'},
        {'readings': 'ChatReading.member'}
    )

    indexes = {
        'uniq_member': {'fields': ['room', 'player'], 'unique': True}
    }

    @after_insert
    def initialise_readings(self, fields, rid):
        rid.readings.create(room=fields.room)


class ChatMessage(TSModel):
    belongs_to({'room': 'ChatRoom'})
    refers_to({'sender': 'ChatMember'})
    has_many({'readings': 'ChatReading'})

    text = Field.text()

    validation = {
        'text': {'presence': True}
    }

    indexes = {
        'room': True,
        'sender': True
    }

    @after_insert
    def update_readings(self, fields, rid):
        if fields.sender:
            ChatReading.where(
                lambda m:
                    (m.room == fields.room) & (m.member == fields.sender)
            ).update(message=rid)


class ChatReading(TSModel):
    belongs_to(
        {'room': 'ChatRoom'},
        {'member': 'ChatMember'}
    )
    refers_to({'message': 'ChatMessage'})

    indexes = {
        'uniq_member': {'fields': ['room', 'member'], 'unique': True},
        'message': True
    }
