from collections.abc import Callable
from dataclasses import dataclass


KEY_LENGTH = 32

_kinds = {}


@dataclass(frozen=True, slots=True)
class Kind:
    key: str
    label: str
    text: Callable[[dict], str]
    #: the notification row -> the URL the item leads to; called in the web app only (it may use `url()`)
    action: Callable[..., str] | None = None


def register(kind):
    if len(kind.key) > KEY_LENGTH:
        raise ValueError(f"Notification kind key longer than {KEY_LENGTH} characters: {kind.key}")
    if kind.key in _kinds:
        raise ValueError(f"Notification kind already registered: {kind.key}")
    _kinds[kind.key] = kind
    return kind


def get(key):
    return _kinds[key]


def kinds():
    return list(_kinds.values())
