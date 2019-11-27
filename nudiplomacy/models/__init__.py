# -*- coding: utf-8 -*-

from emmett import now
from emmett.orm import Model, Field


class TSModel(Model):
    created_at = Field.datetime(notnull=True)
    updated_at = Field.datetime(notnull=True)

    default_values = {
        'created_at': now,
        'updated_at': now
    }

    update_values = {
        'updated_at': now
    }

    fields_rw = {
        'created_at': False,
        'updated_at': False
    }
