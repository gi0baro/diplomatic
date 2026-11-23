from emmett import T, now
from emmett.orm import Field, belongs_to

from ..helpers.choice import Choice
from . import TSModel, UUIDModel


class Notification(TSModel, UUIDModel):
    belongs_to("user")

    class Delivery(Choice):
        PENDING = 0, T("Pending")
        SENT = 1, T("Sent")
        SKIPPED = 2, T("Skipped")

    kind = Field.string(length=32, notnull=True)
    subject_type = Field.string()
    subject_id = Field.string()
    data = Field.json(notnull=True)
    delivered_at = Field.datetime(notnull=True)
    read_at = Field.datetime()
    delivery = Field.int(notnull=True)

    validation = {
        "delivery": {"in": Delivery.choices()},
        "data": {"presence": False},
        "read_at": {"allow": "empty"},
    }

    repr_values = {"delivery": Delivery.repr()}

    indexes = {
        "user_delivered": {"fields": ["user", "delivered_at"]},
        "unread": {"fields": ["user", "kind", "subject_type", "subject_id"], "where": lambda m: m.read_at == None},
        "pending": {"fields": ["created_at"], "where": lambda m: m.delivery == m.Delivery.PENDING},
    }

    @classmethod
    def _unread(cls, user, subject_type, subject_id, kinds):
        return cls.where(
            lambda n: (
                (n.user == user)
                & (n.subject_type == subject_type)
                & (n.subject_id == subject_id)
                & n.kind.belongs(kinds)
                & (n.read_at == None)
            )
        )

    @classmethod
    def emit(cls, user, subject_type, subject_id, kind, data):
        # The UPDATE holds its row locks until the caller commits: emit at the end of the transaction.
        moment = now()
        if cls._unread(user, subject_type, subject_id, [kind]).update(data=data, delivered_at=moment):
            return
        cls.create(
            user=user,
            kind=kind,
            subject_type=subject_type,
            subject_id=subject_id,
            data=data,
            created_at=moment,
            delivered_at=moment,
            delivery=cls.Delivery.PENDING,
        )

    @classmethod
    def read(cls, user, subject_type, subject_id, kinds):
        return cls._unread(user, subject_type, subject_id, kinds).update(read_at=now())

    @classmethod
    def unread_count(cls, user):
        return cls.where(lambda n: (n.user == user) & (n.read_at == None)).count()

    @classmethod
    def latest(cls, user, limitby):
        return cls.where(lambda n: n.user == user).select(orderby=~cls.delivered_at | ~cls.id, limitby=limitby)

    @classmethod
    def due(cls, before):
        rows = (
            cls.where(lambda n: (n.delivery == cls.Delivery.PENDING) & (n.created_at <= before))
            .join("user")
            .select(orderby=cls.created_at | cls.id)
        )
        if not rows:
            return []
        users = list({row.user.id for row in rows})
        settings = {s.user: s for s in NotificationSettings.where(lambda s: s.user.belongs(users)).select()}
        rv = []
        for row in rows:
            user_settings = settings[row.user.id]
            wanted = (
                row.read_at is None and user_settings.email_enabled and row.kind not in user_settings.email_disabled
            )
            rv.append((row, cls.Delivery.SENT if wanted else cls.Delivery.SKIPPED))
        return rv

    @classmethod
    def decide(cls, row, delivery):
        # As Game.claim: one conditional UPDATE, so of two overlapping passes only one moves the row out of
        # PENDING (the other waits for its commit, then matches nothing), and a row read meanwhile is never SENT.
        query = cls.where(lambda n: (n.id == row.id) & (n.delivery == cls.Delivery.PENDING))
        if delivery == cls.Delivery.SENT:
            query = query.where(lambda n: n.read_at == None)
        return bool(query.update(delivery=delivery))

    @classmethod
    def purge(cls, before):
        return cls.where(lambda n: n.delivered_at < before).delete()


class NotificationSettings(TSModel):
    tablename = "notification_settings"

    belongs_to("user")

    email_enabled = Field.bool(notnull=True)
    email_disabled = Field.json(notnull=True)

    validation = {"email_disabled": {"presence": False}}

    default_values = {"email_enabled": True, "email_disabled": []}

    indexes = {"uniq_user": {"fields": ["user"], "unique": True}}
