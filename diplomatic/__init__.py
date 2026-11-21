import os

from celery import Celery
from emmett import App
from emmett.cache import Cache, RamCache, RedisCache
from emmett.orm import Database
from emmett.sessions import SessionManager
from emmett.tools import Auth
from redis import Redis

from .helpers.config import load_config, parse_celery_cron
from .helpers.redis_ext import Redis as RedisExtension


app = App(__name__)
app.languages = ["en", "it"]
app.language_default = "en"
app.language_force_on_url = True
load_config(app)

redis = Redis(**app.config.redis)
cache = Cache(ram=RamCache(), redis=RedisCache(**app.config.redis))

db = Database(app)

from .models.chat import ChatMember, ChatMessage, ChatReading, ChatRoom
from .models.economy import Transaction, Vault
from .models.game import Game, GamePhase, GameRole, Order
from .models.map import Map
from .models.notification import Notification, NotificationSettings
from .models.stats import StatsCountries, StatsEvent, StatsGames, StatsTime
from .models.user import User, UserStats


auth = Auth(app, db, user_model=User)

db.define_models(
    UserStats,
    Map,
    Game,
    GameRole,
    GamePhase,
    Order,
    ChatRoom,
    ChatMember,
    ChatMessage,
    ChatReading,
    Vault,
    Transaction,
    StatsEvent,
    StatsCountries,
    StatsGames,
    StatsTime,
    Notification,
    NotificationSettings,
)

celery = Celery("diplomatic", broker=app.config.worker.broker)
celery.conf.task_default_queue = "default"
celery.conf.task_serializer = "pickle"
celery.conf.accept_content = ["pickle"]
celery.conf.timezone = "UTC"
celery.conf.broker_transport_options = {"visibility_timeout": 60 * 60 * 24}
celery.conf.beat_schedule = parse_celery_cron(app.config.worker.get("cron", {}))

sessions = SessionManager.cookies("foobar")

app.use_extension(RedisExtension)

from . import commands, game_kinds, tasks
