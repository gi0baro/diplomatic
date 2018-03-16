# -*- coding: utf-8 -*-

from celery import Celery
from redis import Redis
from weppy import App
from weppy.cache import Cache, RamCache, RedisCache
from weppy.orm import Database
from weppy.sessions import SessionManager
from weppy.tools import Auth
from weppy_assets import Assets
from weppy_bs3 import BS3
from weppy_haml import Haml
from .helpers.config import parse_celery_cron

app = App(__name__)
app.languages = ['en', 'it']
app.language_default = 'en'
app.language_force_on_url = True
app.config.url_default_namespace = "main"
app.config.Haml.set_as_default = True
app.config_from_yaml('app.yml')
app.config_from_yaml('db.yml', 'db')
app.config.auth.registration_verification = False
app.config.auth.hmac_key = "foobar"

redis = Redis(**app.config.redis)

cache = Cache(
    ram=RamCache(),
    redis=RedisCache(**app.config.redis))

# db and auth
# from .models.system import SysProp, SysJoincode
# from .models.user import User, UserData, UserSettings
# from .models.game import Game, Orders, Chat
# from .models.notification import NObject, NEvent, NSubscription
# from .models.stats import TimeStats, GameStats, CountryStats

db = Database(app)

from .models.user import User, UserStats
from .models.map import Map
from .models.game import Game, GameRole, GamePhase, Order
from .models.economy import Vault, Transaction
from .models.system import SysProp

auth = Auth(app, db, user_model=User)

db.define_models(
    UserStats,
    Map, Game, GameRole, GamePhase, Order,
    Vault, Transaction,
    SysProp)

# db = DAL(app, pool_size=5, adapter_args={'uploads_in_blob': True})

celery = Celery('nudiplomacy', broker=app.config.celery.broker)
celery.conf.task_default_queue = 'default'
celery.conf.task_serializer = 'pickle'
celery.conf.accept_content = ['pickle']
celery.conf.timezone = 'UTC'
celery.conf.broker_transport_options = {'visibility_timeout': 60 * 60 * 24}
celery.conf.beat_schedule = parse_celery_cron(app.config.celery.get('cron_tasks', {}))


app.pipeline = [
    # SessionManager.redis(redis),
    SessionManager.cookies('foobar'),
    db.pipe,
    auth.pipe
]

# extensions
app.use_extension(Haml)
app.use_extension(Assets)
app.use_extension(BS3)

# routes
# from .controllers import main, admin, games, maps, api
from .controllers import main, maps, games, api

# auth.settings.login_next = url('games.index')

from . import assets
from . import commands
from . import tasks
