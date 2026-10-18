from emmett import response

from .. import UserStats, app, cache, db
from . import front


@front.route("/")
def index():
    return {"participating": []}


# @app.route()
# def regcode():
#     def proc_form(form):
#         if not form.params.code:
#             form.errors.code = "You need a code to register"
#             return
#         row = db.SysJoincode(code=form.params.code)
#         if not row:
#             form.errors.code = "Code you provided is not valid"
#             return
#         if not row.active or row.count >= row.limit:
#             form.errors.code = "Code you provided is no longer active"
#             return
#         mdb.sys_actcodes.upd({'id': row.id}, {'$inc': {'count': 1}})

#     form = Form(Field("code"), onvalidation=proc_form)
#     if form.accepted:
#         session.regCode = form.params.code
#         redirect(url("account", "register"))
#     return dict(form=form)


RANKING_SIZE = 100
RANKING_TTL = 300


def top_ranks():
    return UserStats.all().select(
        orderby=~UserStats.score | ~UserStats.points, paginate=(1, RANKING_SIZE), including="user"
    )


@front.route()
def ranking():
    return {"ranks": cache("ranking", top_ranks, RANKING_TTL)}


# @app.route(helpers=[AppStatus(), BaseContext()])
# def stats():
#     active = db(db.Game.active == True).count()
#     completed = db((db.Game.active == False) &
#                    (db.Game.status != "pregame")).count()
#     pvariants = []
#     return locals()


@app.route("/download/<str:filename>", pipeline=[db.pipe])
def download(filename):
    return response.wrap_dbfile(db, filename)
