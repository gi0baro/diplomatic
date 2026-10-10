# -*- coding: utf-8 -*-

from emmett import AppModule, url
from emmett.pipeline import RequirePipe

from diplomatic import SysJoincode, app, auth, cache, db, mdb
from diplomatic.contexts import BaseContext
from diplomatic.helpers.system import isAppOnline


admin = AppModule(app, "admin", __name__, url_prefix="admin", template_folder="admin")
admin.common_helpers = [BaseContext(), RequirePipe(lambda: auth.has_membership("admin"), url("index"))]


@admin.route("/")
def index():
    online = "online" if isAppOnline() else "offline"
    return dict(online=online)


@admin.route("/a/appstatus")
def change_appstatus():
    status = isAppOnline()
    newstatus = not status
    mdb.sys_prop.upd({"name": "sys_online"}, {"$set": {"data.value": newstatus}})
    # temp fix for emmett
    # cache.redis.clear('sys_online')
    cache.redis._cache.delete(cache.redis._prefix + "sys_online")
    if newstatus:
        return "$('#online-status').html('online');"
    return "$('#online-status').html('offline');"


@admin.route()
def regcodes():
    codes = db(db.SysJoincode.id > 0).select()
    form = SysJoincode.form()
    return locals()


@admin.route()
def notifications():
    objs = mdb.notification_objects.find({})
    events = mdb.notification_events.find({})
    subs = mdb.notification_subscriptions.find({})
    return locals()
