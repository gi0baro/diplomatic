from emmett_assets import Assets
from emmett_haml import Haml

from . import app, db


app.use_extension(Haml)
app.use_extension(Assets)

from . import assets, controllers
