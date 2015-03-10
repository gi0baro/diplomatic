from weppy import AppModule, url, abort, Form, Field
from weppy.tools import requires
from nudiplomacy import app, auth, db, Map
from nudiplomacy.handlers import AppStatus
from nudiplomacy.contexts import BaseContext

maps = AppModule(app, "maps", __name__, url_prefix="maps",
                 template_folder="maps")
maps.common_helpers = [AppStatus(), BaseContext()]


@maps.expose("/")
def index():
    rows = db(db.Map.id > 0).select()
    return dict(maps=rows)


@maps.expose("/<int:mid>")
def details(mid):
    row = db.Map(id=mid)
    app.log.debug(row.as_dict()['neutrals'])
    return dict(map=row)


@maps.expose()
@requires(auth.is_logged_in, url("main.index"))
def new():
    return dict(form=Map.form())


@maps.expose()
@requires(auth.is_logged_in, url("main.index"))
def newffile():
    fields = [
        Field("image", "upload"),
        Field("data", "json")
    ]
    form = Form(*fields)
    if form.accepted:
        import json
        jdata = json.loads(form.vars.data)
        db.Map.insert(
            image=db.Map.image.store(form.vars.image.file,
                                     form.vars.image.filename),
            image_blob=form.vars.image.file.read(),
            **jdata)
    return dict(form=form)


@maps.expose("/edit/<int:mid>", template="new.haml")
@requires(lambda: auth.has_membership('admin'), url("main.index"))
def edit(mid):
    record = db.Map(id=mid)
    if not record:
        abort(404)
    return dict(form=Map.form(record))
