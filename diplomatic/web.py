from emmett_assets import Assets
from emmett_haml import Haml

from . import app
from .exts.bs3 import BS3


app.use_extension(Haml)
app.use_extension(Assets)
app.use_extension(BS3)

from . import assets, controllers
