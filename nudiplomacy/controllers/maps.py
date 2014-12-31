from weppy import AppModule, url, abort
from weppy.tools import requires
from nudiplomacy import app, auth, db, Map
from nudiplomacy.contexts import BaseContext

maps = AppModule(app, "maps", __name__, url_prefix="maps",
                 template_folder="maps")
maps.common_helpers = [BaseContext()]


@maps.expose("/")
def index():
    #temp
    rows = db(db.Map.id > 0).select().as_list()
    app.log.debug(rows)
    #
    return dict()


@maps.expose()
@requires(auth.is_logged_in, url("main.index"))
def new():
    return dict(form=Map.form())


@maps.expose("/edit/<int:mid>", template="new.haml")
@requires(lambda: auth.has_membership('admin'), url("main.index"))
def edit(mid):
    record = db.Map(id=mid)
    if not record:
        abort(404)
    return dict(form=Map.form(record))
