from collections.abc import Callable
from dataclasses import dataclass


KEY_LENGTH = 32
EMAIL_SUBJECT = "Diplomatic: {}"
#: the web app's paths of the open route and of the account page (the email settings), for links built
#: without `url()`: the default language has no prefix on the URL
OPEN_PATH = "/notifications/{}/open"
SETTINGS_PATH = "/account/profile"
SETTINGS_LINE = "Email settings: {}"

_kinds = {}


@dataclass(frozen=True, slots=True)
class Kind:
    key: str
    label: str
    text: Callable[[dict], str]
    #: the email, English only (the worker does not know the reader's language): `data` -> subject, plain-text body
    subject: Callable[[dict], str]
    body: Callable[[dict], str]
    #: the notification row -> the URL the item leads to; called in the web app only (it may use `url()`)
    action: Callable[..., str] | None = None
    #: introduces the email's link to the call to action ("Open the game:")
    link_label: str | None = None


def register(kind):
    if len(kind.key) > KEY_LENGTH:
        raise ValueError(f"Notification kind key longer than {KEY_LENGTH} characters: {kind.key}")
    if kind.key in _kinds:
        raise ValueError(f"Notification kind already registered: {kind.key}")
    if bool(kind.action) != bool(kind.link_label):
        raise ValueError(f"Notification kind {kind.key}: a link label goes with a call to action, and only with one")
    _kinds[kind.key] = kind
    return kind


def get(key):
    return _kinds[key]


def kinds():
    return list(_kinds.values())


def email(notification, site):
    #: the frame, the same for every kind: (subject, body); `site` is the site's public address
    kind = get(notification.kind)
    parts = [kind.body(notification.data)]
    if kind.action:
        parts.append(f"{kind.link_label} {site}{OPEN_PATH.format(notification.id)}")
    parts.append(SETTINGS_LINE.format(site + SETTINGS_PATH))
    return EMAIL_SUBJECT.format(kind.subject(notification.data)), "\n\n".join(parts)
