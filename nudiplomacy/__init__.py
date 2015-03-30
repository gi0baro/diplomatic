from weppy import App, DAL, url
from weppy.cache import Cache, RamCache, RedisCache
from weppy.sessions import SessionRedisManager
from weppy.tools import Auth

app = App(__name__)
app.config.url_default_namespace = "main"
app.config.Haml.set_as_default = True

# languages
app.languages = ['en', 'it']
app.language_default = 'en'
app.language_force_on_url = True

## load config
app.config_from_yaml('app.yml')
app.config_from_yaml('db.yml', 'db')

# redis and queue system
from redis import Redis
redis = Redis(host=app.config.redis.host, port=app.config.redis.port,
              db=app.config.redis.db)
from helpers.queues import Queue
queue = Queue(app, redis)

cache = Cache(
    ram=RamCache(),
    redis=RedisCache(
        host=app.config.redis.host, port=app.config.redis.port,
        db=app.config.redis.db))

# db and auth
from models.system import SysProp, SysActCode
from models.user import User, UserData, UserSettings
from models.map import Map
from models.game import Game, Orders, Chat
from models.notification import NObject, NEvent, NSubscription
from models.stats import TimeStats, GameStats, CountryStats
db = DAL(app, pool_size=5, adapter_args={'uploads_in_blob': True})
auth = Auth(app, db, usermodel=User, mailer=False)
db.define_models([
    SysProp, SysActCode, UserData, UserSettings, Map, Game, Orders, Chat,
    NObject, NEvent, NSubscription, TimeStats, GameStats, CountryStats])
from helpers.mongo import MongoDB
mdb = MongoDB(db)

app.expose.common_handlers = [
    SessionRedisManager(redis),
    db.handler,
    auth.handler
]

# extensions
from weppy_haml import Haml
from weppy_assets import Assets
from weppy_bs3 import BS3
app.use_extension(Haml)
app.use_extension(Assets)
app.use_extension(BS3)

# routes
from controllers import main, admin, games, maps, api

auth.settings.login_next = url('games.index')

import assets
import commands
