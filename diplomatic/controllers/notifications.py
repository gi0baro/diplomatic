from emmett import Field, Form, T, redirect, request, url

from .. import Notification, NotificationSettings, auth, notifications as registry
from . import authenticated, query_page


BELL_SIZE = 5
PAGE_SIZE = 25
WHEN_FORMAT = "%d %b %H:%M UTC"

notifications = authenticated.module(
    __name__, "notifications", url_prefix="notifications", template_folder="notifications"
)


def items_of(rows):
    rv = []
    for row in rows:
        kind = registry.get(row.kind)
        rv.append(
            {
                "text": kind.text(row.data),
                "when": row.delivered_at.strftime(WHEN_FORMAT),
                "unread": row.read_at is None,
                "href": url(".open_item", row.id) if kind.action else None,
            }
        )
    return rv


def read_shown(rows):
    #: the rows keep their unread look for this response
    for row in rows:
        if row.read_at is None and not registry.get(row.kind).action:
            Notification.read(auth.user.id, row.subject_type, row.subject_id, [row.kind])


@notifications.route("/")
def index():
    page = query_page()
    rows = Notification.latest(auth.user.id, ((page - 1) * PAGE_SIZE, page * PAGE_SIZE + 1))
    shown = rows[:PAGE_SIZE]
    read_shown(shown)
    return {"items": items_of(shown), "page": page, "has_next": len(rows) > PAGE_SIZE}


@notifications.route("/bell", template="partials/bell.haml")
def partial_bell():
    rows = Notification.latest(auth.user.id, (0, BELL_SIZE))
    read_shown(rows)
    return {"items": items_of(rows), "unread": Notification.unread_count(auth.user.id)}


@notifications.route("/<str:nid>/open")
def open_item(nid):
    row = Notification.get(id=nid, user=auth.user.id)
    if not row:
        redirect(url(".index"))
    Notification.read(auth.user.id, row.subject_type, row.subject_id, [row.kind])
    action = registry.get(row.kind).action
    if not action:
        redirect(url(".index"))
    redirect(action(row))


def kind_field(key):
    return "kind_" + key.replace(".", "_")


def settings_form(settings):
    fields = {"email_enabled": Field.bool(default=settings.email_enabled, label=T("All emails"))}
    for kind in registry.kinds():
        fields[kind_field(kind.key)] = Field.bool(default=kind.key not in settings.email_disabled, label=kind.label)
    return Form(fields)


@notifications.route("/settings", methods=["get", "post"], template="partials/settings.haml")
async def partial_settings():
    settings = NotificationSettings.get(user=auth.user.id)
    form = await settings_form(settings)
    if form.accepted:
        settings.update_record(
            email_enabled=form.params.email_enabled,
            email_disabled=[kind.key for kind in registry.kinds() if not form.params[kind_field(kind.key)]],
        )
        redirect(url(".partial_settings", params={"saved": 1}))
    return {
        "form": form,
        "fields": [kind_field(kind.key) for kind in registry.kinds()],
        "saved": bool(request.query_params.saved),
    }
