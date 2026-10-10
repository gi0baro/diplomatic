# -*- coding: utf-8 -*-

from emmett import abort

# from diplomatic import app, auth, db, Map
# from diplomatic.handlers import AppStatus
# from diplomatic.contexts import BaseContext
from .. import Map
from . import front


maps = front.module(__name__, "maps", url_prefix="maps", template_folder="maps")


@maps.route("/")
def index():
    rows = Map.all_latest().select(Map.table.ALL, orderby=Map.name)
    return {"maps": rows}


@maps.route("/<int:mid>")
def detail(mid):
    row = Map.get(mid)
    if not row:
        abort(404)
    return {"map": row}


# @maps.route()
# @requires(auth.is_logged_in, url("main.index"))
# def new():
#     return dict(form=Map.form())


# @maps.route()
# @requires(auth.is_logged_in, url("main.index"))
# def newffile():
#     fields = {
#         'image': Field("upload"),
#         'data': Field("json")
#     }
#     form = Form(fields)
#     if form.accepted:
#         jdata = form.params.data
#         db.Map.insert(
#             image=db.Map.image.store(form.params.image.file, form.params.image.filename),
#             image_blob=form.params.image.file.read(),
#             **jdata)
#     return dict(form=form)


# @maps.route("/edit/<int:mid>", template="new.haml")
# @requires(lambda: auth.has_membership('admin'), url("main.index"))
# def edit(mid):
#     record = Map.get(mid)
#     if not record:
#         abort(404)
#     return dict(form=Map.form(record))
