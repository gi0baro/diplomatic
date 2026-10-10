# -*- coding: utf-8 -*-

from .. import SysProp, cache


@cache(duration=300)
def system_property(name, key="value", default=None):
    row = SysProp.get(name=name)
    if not row:
        return default
    return row.data.get(key, default)
