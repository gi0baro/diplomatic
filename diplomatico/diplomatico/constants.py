from enum import IntEnum


class Phase(IntEnum):
    DIPLOMACY = 0
    RETREATS = 1
    BUILDS = 2


class Season(IntEnum):
    SPRING = 0
    AUTUMN = 1


class OrderType(IntEnum):
    HOLD = 0
    MOVE = 1
    SUPPORT_HOLD = 2
    SUPPORT_MOVE = 3
    CONVOY = 4
    RETREAT = 5
    BUILD = 6
    DISBAND = 7


class Troop(IntEnum):
    ARMY = 0
    FLEET = 1
