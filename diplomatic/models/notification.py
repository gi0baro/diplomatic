# -*- coding: utf-8 -*-

from emmett import session
from emmett.dal import Field, Model, belongs_to

from diplomatic.helpers.mongo import longToObjid, objidToLong


class NObject(Model):
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

    channel = Field()
    type = Field()

    @classmethod
    def get_one(cls, channel=None, t=None):
        _query = (cls.channel == channel) & (cls.type == t)
        return cls.db(_query).select().first()


class NEvent(Model):
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

    belongs_to({"object": "NObject"}, {"recipient": "User"})

    actor = Field()
    data = Field("json")
    occurred_at = Field("datetime")
    is_read = Field("bool", default=False)

    @classmethod
    def find_unread(cls, user=None):
        uid = user or (session.auth.user.id if session.auth else None)
        return cls((cls.recipient == uid) & (cls.is_read == False)).select()


class NSubscription(Model):
    """
    Contains data about single user subscriptions
        `channel`
            identifies the channel user is subscribed to
            example: "user_[id]"
        `objects`
            the types user is subscribed to, referenced to objects
    """

    tablename = "notification_subscriptions"

    belongs_to("user")

    channel = Field()
    objects = Field("list:reference notification_objects")

    @classmethod
    def find_subscribers(cls, channel, nobj):
        from diplomatic import mdb

        rows = mdb.notification_subscriptions.find({"channel": channel, "objects": longToObjid(nobj.id)})
        return [objidToLong(row.user) for row in rows]

    @classmethod
    def subscribe(cls, user, channel, nobj=None, nid=None):
        from diplomatic import mdb

        if nid:
            nid = longToObjid(nid)
        else:
            nid = longToObjid(nobj.id)
        mdb.notification_subscriptions.ioru(
            {"user": longToObjid(user), "channel": channel}, {"$push": {"objects": nid}}
        )

    @classmethod
    def unsuscribe(cls, channel, objs, user=None):
        uid = user or (session.auth.user.id if session.auth else None)
        if objs == "all":
            _query = (cls.channel == channel) & (cls.user == uid)
            cls.db(_query).update(objects=[])
        else:
            if not isinstance(objs, list):
                objs = [objs]
            from diplomatic import mdb

            mdb.notification_subscriptions.fandm(
                {"user": longToObjid(uid), "channel": channel}, {"$pull": {"objects": objs}}
            )
