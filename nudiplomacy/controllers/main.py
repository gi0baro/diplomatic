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


@app.expose("/download/<str:filename>")
def download(filename):
    stream_dbfile(db, filename)
