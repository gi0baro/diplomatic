# -*- coding: utf-8 -*-

from weppy.dal import Model, Field


class SysProp(Model):
    tablename = "sys_prop"

    fields = [
        Field("name", "string"),
        Field("data", "json")
    ]
