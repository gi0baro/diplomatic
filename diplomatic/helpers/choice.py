from enum import IntEnum


class Choice(IntEnum):
    def __new__(cls, value, label):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.label = label
        return obj

    def __repr__(self):
        return repr(self.value)

    @classmethod
    def choices(cls):
        return [(member, member.label) for member in cls]

    @classmethod
    def repr(cls):
        return lambda value: cls(value).label
