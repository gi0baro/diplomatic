# -*- coding: utf-8 -*-

from nudiplomacy import db, cache


def _readProp(name, defval):
    row = db(db.SysProp.name == name).select().first()
    if row:
        return row.data.get('value', defval)
    db.SysProp.insert(name=name, data={"value": defval})
    return defval


def isAppOnline():
    return cache.redis('sys_online', lambda: _readProp("sys_online", True),
                       None)
