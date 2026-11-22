from collections.abc import Callable
from dataclasses import dataclass

from renoir import Renoir

from .. import app


EMAIL_SUBJECT = "Diplomatic: {}"
#: the web app's paths of the open route and of the account page (the email settings), for links built
#: without `url()`: the default language has no prefix on the URL
OPEN_PATH = "/notifications/{}/open"
SETTINGS_PATH = "/account/profile"

_kinds = {}
_templates = Renoir(path=app.template_path, mode="plain", reload=app.debug)


@dataclass(frozen=True, slots=True)
class Kind:
    key: str
    label: str
    text: Callable[[dict], str]
    #: English only, as the email body (`templates/emails/<key>.txt`): the worker does not know the reader's language
    subject: str
    context: Callable[[dict], dict] | None = None
    #: called in the web app only (it may use `url()`)
    action: Callable[..., str] | None = None


def register(kind):
    _kinds[kind.key] = kind


def get(key):
    return _kinds[key]


def kinds():
    return list(_kinds.values())


def email(notification, site):
    kind = get(notification.kind)
    context = kind.context(notification.data) if kind.context else dict(notification.data)
    context.update(link=site + OPEN_PATH.format(notification.id), settings=site + SETTINGS_PATH)
    body = _templates.render(f"emails/{kind.key}.txt", context)
    return EMAIL_SUBJECT.format(kind.subject.format(**context)), body


from . import games
