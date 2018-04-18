# -*- coding: utf-8 -*-

from .helpers import adict


PHASES = adict(
    DIPLOMACY=0,
    RETREATS=1,
    BUILDS=2
)

ORDERS = adict(
    HOLD=0,
    MOVE=1,
    SUPPORT_HOLD=2,
    SUPPORT_MOVE=3,
    CONVOY=4,
    RETREAT=5,
    BUILD=6,
    DISBAND=7
)
