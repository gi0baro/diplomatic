# -*- coding: utf-8 -*-

from weppy import session
from weppy.dal import Field, Model, modelmethod
from nudiplomacy.helpers.mongo import longToObjid, objidToLong


class Object(Model):
    """
    Contains main data about notifications
        `type`
            identifies the type of notification for example:
            "game_processed", "game_message"
        `channel`
            identifies the recipient(s) for the notification, for example:
            "user_[id]", "game_[id]"
    """
    tablename = "notification_objects"

    fields = [
        Field("channel", "string"),
        Field("type", "string")
    ]

    @modelmethod
    def get_one(db, entity, channel=None, t=None):
        _query = (entity.channel == channel) & (entity.type == t)
        return db(_query).select().first()


class Event(Model):
    """
    Contains data about single user notification
        `object`
            is the id of Object table
        `actor`
            identifies who is the actor, for example:
            "gi0baro" (notif. like "gi0baro sent you a message")
            "game 123" (notif. like "There are 3 new messages on game 123")
        `data`
            what happened? for example:
            {"msg":"sent message", type: "user", "pic": imgurl}
            {"msg":"new turn", type: "game", "pic": imgurl}
    """
    tablename = "notification_events"

    fields = [
        Field("object", "reference notification_objects"),
        Field("recipient", "reference auth_user"),
        Field("actor", "string"),
        Field("data", "json"),
        Field("date", "datetime"),
        Field("read", "boolean", default=False)
    ]

    @modelmethod
    def find_unread(db, entity, user=None):
        uid = user or (session.auth.user.id if session.auth else None)
        return db((entity.recipient == uid) & (entity.read == False)).select()


class Subscription(Model):
    """
    Contains data about single user subscriptions
        `channel`
            identifies the channel user is subscribed to
            example: "user_[id]"
        `objects`
            the types user is subscribed to, referenced to objects
    """
    tablename = "notification_subscriptions"

    fields = [
        Field("user", "reference auth_user"),
        Field("channel", "string"),
        Field("objects", "list:reference notification_objects")
    ]

    @modelmethod
    def find_subscribers(db, entity, channel, obj):
        from nudiplomacy import mdb
        rows = mdb.notification_subscriptions.find(
            {"channel": channel, "objects": longToObjid(obj)})
        return [objidToLong(row.user) for row in rows]

    @modelmethod
    def unsuscribe(db, entity, channel, objs, user=None):
        uid = user or (session.auth.user.id if session.auth else None)
        if objs == "all":
            _query = (entity.channel == channel) & (entity.user == uid)
            db(_query).update(objects=[])
        else:
            if not isinstance(objs, list):
                objs = [objs]
            from nudiplomacy import mdb
            mdb.notification_subscriptions.fandm(
                {"user": longToObjid(uid), "channel": channel},
                {"$pull": {"objects": objs}}
            )
