from weppy import session, redirect, url, Form, Field
from weppy.helpers import stream_dbfile
from nudiplomacy import app, auth, db, mdb, Game
from nudiplomacy.handlers import AppStatus
from nudiplomacy.contexts import BaseContext


@app.route("/", helpers=[AppStatus(), BaseContext()])
def index():
    participating = Game.participating() if auth.user else []
    return dict(participating=participating)


@app.route("/account(/<str:f>)?(/<str:k>)?", helpers=[BaseContext()])
def account(f, k):
    if f == "register" and app.config.registration_codes:
        if not session.regCode:
            redirect(url("regcode"))
    if f != "register" and session.regCode:
        del session.regCode
    form = auth(f, k)
    return dict(form=form, req=f)


@app.route(helpers=[BaseContext()])
def regcode():
    def proc_form(form):
        if not form.params.code:
            form.errors.code = "You need a code to register"
            return
        row = db.SysJoincode(code=form.params.code)
        if not row:
            form.errors.code = "Code you provided is not valid"
            return
        if not row.active or row.count >= row.limit:
            form.errors.code = "Code you provided is no longer active"
            return
        mdb.sys_actcodes.upd({'id': row.id}, {'$inc': {'count': 1}})

    form = Form(Field("code"), onvalidation=proc_form)
    if form.accepted:
        session.regCode = form.params.code
        redirect(url("account", "register"))
    return dict(form=form)


@app.route(helpers=[AppStatus(), BaseContext()])
def ranking():
    rlist = db(db.UserData.id > 0).select(
        orderby=~db.UserData.points, limitby=(0, 100))
    return dict(ranks=rlist)


@app.route(helpers=[AppStatus(), BaseContext()])
def stats():
    active = db(db.Game.active == True).count()
    completed = db((db.Game.active == False) &
                   (db.Game.status != "pregame")).count()
    pvariants = []
    return locals()


@app.route("/download/<str:filename>")
def download(filename):
    stream_dbfile(db, filename)
