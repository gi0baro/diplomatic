from weppy.helpers import stream_dbfile
from nudiplomacy import app, auth, db, Game
from nudiplomacy.contexts import BaseContext


@app.expose("/", helpers=[BaseContext()])
def index():
    participating = []
    if auth.user:
        participating = Game.participating()
    return dict(participating=participating)


@app.expose("/account(/<str:f>)?(/<str:k>)?", helpers=[BaseContext()])
def account(f, k):
    form = auth(f, k)
    return dict(form=form, req=f)


@app.expose(helpers=[BaseContext()])
def ranking():
    rlist = db(db.UserData.id > 0).select(
        orderby=~db.UserData.points, limitby=(0, 100))
    return dict(ranks=rlist)


@app.expose(helpers=[BaseContext()])
def stats():
    active = db(db.Game.active == True).count()
    completed = db((db.Game.active == False) &
                   (db.Game.status != "pregame")).count()
    pvariants = []
    return locals()


@app.expose("/download/<str:filename>")
def download(filename):
    stream_dbfile(db, filename)
