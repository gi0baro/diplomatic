# -*- coding: utf-8 -*-

from weppy.dal import Model, Field


class SysProp(Model):
    name = Field()
    data = Field('json')


class SysJoincode(Model):
    code = Field()
    limit = Field('int', default=50)
    count = Field('int', default=0)
    active = Field('bool')
