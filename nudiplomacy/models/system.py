# -*- coding: utf-8 -*-

from weppy.orm import Model, Field


class SysProp(Model):
    name = Field(notnull=True, unique=True)
    data = Field.json()

    indexes = {
        'uniq_name': {'fields': ['name'], 'unique': True}
    }


# class SysJoincode(Model):
#     code = Field()
#     limit = Field('int', default=50)
#     count = Field('int', default=0)
#     active = Field('bool')
