from emmett_haml import Haml

from . import app, db


app.use_extension(Haml)

from . import controllers
