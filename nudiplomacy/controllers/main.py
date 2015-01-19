from weppy.helpers import stream_dbfile
from nudiplomacy import app, auth, db
from nudiplomacy.contexts import BaseContext


@app.expose("/", helpers=[BaseContext()])
def index():
    return dict()


@app.expose("/account(/<str:f>)?(/<str:k>)?", helpers=[BaseContext()])
def account(f, k):
    form = auth(f, k)
    return dict(form=form, req=f)


@app.expose("/download/<str:filename>")
def download(filename):
    stream_dbfile(db, filename)
