# -*- coding: utf-8 -*-

from weppy import AppModule, url
from weppy.handlers import RequireHandler
from nudiplomacy import app, db, mdb, auth, cache, SysJoincode
from nudiplomacy.contexts import BaseContext
from nudiplomacy.helpers.system import isAppOnline

admin = AppModule(app, "admin", __name__, url_prefix="admin",
                  template_folder="admin")
admin.common_helpers = [
    BaseContext(),
    RequireHandler(lambda: auth.has_membership('admin'), url('index'))]


@admin.route("/")
def index():
    online = "online" if isAppOnline() else "offline"
    return dict(online=online)


@admin.route("/a/appstatus")
def change_appstatus():
    status = isAppOnline()
    newstatus = not status
    mdb.sys_prop.upd(
        {'name': 'sys_online'}, {'$set': {'data.value': newstatus}})
    # temp fix for weppy
    #cache.redis.clear('sys_online')
    cache.redis._cache.delete(cache.redis._prefix+"sys_online")
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
