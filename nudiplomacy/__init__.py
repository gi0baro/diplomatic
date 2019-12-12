# -*- coding: utf-8 -*-

import os

from celery import Celery
from redis import Redis
from emmett import App
from emmett.cache import Cache, RamCache, RedisCache
from emmett.orm import Database
from emmett.sessions import SessionManager
from emmett.tools import Auth
from emmett_assets import Assets
# from emmett_bs3 import BS3
from emmett_haml import Haml

from .exts.bs3 import BS3
from .helpers import postgres
from .helpers.config import parse_celery_cron
from .helpers.redis_ext import Redis as RedisExtension

app = App(__name__)
app.languages = ['en', 'it']
app.language_default = 'en'
app.language_force_on_url = True
app.config.url_default_namespace = "main"
app.config.static_version_urls = True
app.config.static_version = '0.1.0'
app.config.Haml.set_as_default = True
app.config_from_yaml('app.yml')
# app.config_from_yaml('db.yml', 'db')
app.config.auth.registration_verification = False
app.config.auth.hmac_key = "foobar"

app.config.db.host = os.environ.get('POSTGRES_HOST', 'localhost')
app.config.db.user = os.environ.get('POSTGRES_USER', 'postgres')
app.config.db.password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
app.config.db.database = os.environ.get('POSTGRES_DB', app.name)
app.config.db.pool_size = int(os.environ.get('POSTGRES_POOL_SIZE', 0))
app.config.redis.host = os.environ.get('REDIS_HOST', 'localhost')
app.config.redis.port = int(os.environ.get('REDIS_PORT', 6379))
app.config.worker.broker = os.environ.get('WRK_BROKER_URL', 'redis://localhost:6379/1')

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
from .models.chat import ChatRoom, ChatMember, ChatMessage, ChatReading
from .models.economy import Vault, Transaction
from .models.system import SysProp

auth = Auth(app, db, user_model=User)

db.define_models(
    UserStats,
    Map, Game, GameRole, GamePhase, Order,
    ChatRoom, ChatMember, ChatMessage, ChatReading,
    Vault, Transaction,
    SysProp)

# db = DAL(app, pool_size=5, adapter_args={'uploads_in_blob': True})

celery = Celery('nudiplomacy', broker=app.config.worker.broker)
celery.conf.task_default_queue = 'default'
celery.conf.task_serializer = 'pickle'
celery.conf.accept_content = ['pickle']
celery.conf.timezone = 'UTC'
celery.conf.broker_transport_options = {'visibility_timeout': 60 * 60 * 24}
celery.conf.beat_schedule = parse_celery_cron(app.config.worker.get('cron', {}))


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
app.use_extension(RedisExtension)

from . import assets, tasks

# routes
# from .controllers import main, admin, games, maps, api
from .controllers import main, maps, games, api, ws

# auth.settings.login_next = url('games.index')

# from . import assets
from . import commands
# from . import tasks
