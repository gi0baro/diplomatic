import uuid

from emmett import now
from emmett.orm import Field, Model


class TSModel(Model):
    created_at = Field.datetime(notnull=True)
    updated_at = Field.datetime(notnull=True)

    default_values = {"created_at": now, "updated_at": now}

    update_values = {"updated_at": now}

    fields_rw = {"created_at": False, "updated_at": False}


class UUIDModel(Model):
    id = Field.string(length=32, default=lambda: uuid.uuid7().hex)


def wrap_in_atomic(f):
    def wrapped(self, *args, **kwargs):
        with self.db.atomic():
            return f(self, *args, **kwargs)

    return wrapped
