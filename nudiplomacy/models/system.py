# -*- coding: utf-8 -*-

from weppy.dal import Model, Field


class SysProp(Model):
    tablename = "sys_prop"

    fields = [
        Field("name", "string"),
        Field("data", "json")
    ]


class SysActCode(Model):
    tablename = "sys_actcodes"

    fields = [
        Field("code"),
        Field("limit", "integer", default=50),
        Field("count", "integer", default=0),
        Field("active", "boolean", default=True)
    ]
