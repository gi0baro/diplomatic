from weppy import AppModule, url, abort, Form, Field
from weppy.tools import requires
from nudiplomacy import app, auth, db, Map
from nudiplomacy.handlers import AppStatus
from nudiplomacy.contexts import BaseContext

maps = AppModule(app, "maps", __name__, url_prefix="maps",
                 template_folder="maps")
maps.common_helpers = [AppStatus(), BaseContext()]


@maps.route("/")
def index():
    rows = db(db.Map.id > 0).select()
    return dict(maps=rows)


@maps.route("/<int:mid>")
def details(mid):
    row = Map.get(mid)
    app.log.debug(row.as_dict()['neutrals'])
    return dict(map=row)


@maps.route()
@requires(auth.is_logged_in, url("main.index"))
def new():
    return dict(form=Map.form())


@maps.route()
@requires(auth.is_logged_in, url("main.index"))
def newffile():
    fields = {
        'image': Field("upload"),
        'data': Field("json")
    }
    form = Form(fields)
    if form.accepted:
        jdata = form.params.data
        db.Map.insert(
            image=db.Map.image.store(form.params.image.file, form.params.image.filename),
            image_blob=form.params.image.file.read(),
            **jdata)
    return dict(form=form)


@maps.route("/edit/<int:mid>", template="new.haml")
@requires(lambda: auth.has_membership('admin'), url("main.index"))
def edit(mid):
    record = Map.get(mid)
    if not record:
        abort(404)
    return dict(form=Map.form(record))
