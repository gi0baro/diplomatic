from emmett import abort, response

# from diplomatic import app, auth, db, Map
# from diplomatic.handlers import AppStatus
# from diplomatic.contexts import BaseContext
from .. import Map, app, cache, db
from ..helpers.maps import preview_svg as build_preview, thumb_svg as build_thumb
from . import front


maps = front.module(__name__, "maps", url_prefix="maps", template_folder="maps")

#: the SVG documents are public and immutable (a new revision is a new row,
#: hence a new URL), so they live outside `front`: no session cookie on a
#: response any shared cache may store, no auth, no app status check
map_files = app.module(__name__, "map_files", url_prefix="maps")
map_files.pipeline = [db.pipe]


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


def _svg_row(mid, *fields):
    row = Map.where(lambda m: m.id == mid).select(Map.svg, *fields).first()
    if not row or not row.svg:
        abort(404)
    response.content_type = "image/svg+xml"
    response.headers["cache-control"] = "public, max-age=31536000, immutable"
    return row


@map_files.route("/<int:mid>/map.svg")
@cache.response(duration=None)
def map_svg(mid):
    return _svg_row(mid).svg


@map_files.route("/<int:mid>/preview.svg")
@cache.response(duration=None)
def preview_svg(mid):
    return build_preview(_svg_row(mid, Map.names, Map.countries, Map.init))


@map_files.route("/<int:mid>/thumb.svg")
@cache.response(duration=None)
def thumb_svg(mid):
    return build_thumb(_svg_row(mid, Map.names, Map.countries, Map.init))


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
# def edit(mid):
#     record = Map.get(mid)
#     if not record:
#         abort(404)
#     return dict(form=Map.form(record))
