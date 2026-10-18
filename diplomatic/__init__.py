import os

from celery import Celery
from emmett import App
from emmett.cache import Cache, RamCache, RedisCache
from emmett.orm import Database
from emmett.sessions import SessionManager
from emmett.tools import Auth
from redis import Redis

from .helpers.config import parse_celery_cron
from .helpers.redis_ext import Redis as RedisExtension


app = App(__name__)
app.languages = ["en", "it"]
app.language_default = "en"
app.language_force_on_url = True
app.config.url_default_namespace = "main"
app.config.static_version_urls = True
app.config.static_version = "0.1.3"
app.config.Haml.set_as_default = True
app.config_from_yaml("app.yml")
# app.config_from_yaml('db.yml', 'db')
app.config.auth.registration_verification = os.environ.get("AUTH_EMAIL_VERIFICATION", "1") == "1"
app.config.auth.hmac_key = "foobar"
app.config.build_commit = os.environ.get("APP_COMMIT", "dev")

app.config.db.host = os.environ.get("POSTGRES_HOST", "localhost")
app.config.db.user = os.environ.get("POSTGRES_USER", "postgres")
app.config.db.password = os.environ.get("POSTGRES_PASSWORD", "postgres")
app.config.db.database = os.environ.get("POSTGRES_DB", app.name)
app.config.db.pool_size = int(os.environ.get("POSTGRES_POOL_SIZE", 10))
app.config.redis.host = os.environ.get("REDIS_HOST", "localhost")
app.config.redis.port = int(os.environ.get("REDIS_PORT", 6379))
app.config.worker.broker = os.environ.get("WRK_BROKER_URL", "redis://localhost:6379/1")

redis = Redis(**app.config.redis)

cache = Cache(ram=RamCache(), redis=RedisCache(**app.config.redis))

# db and auth
db = Database(app)

from .models.chat import ChatMember, ChatMessage, ChatReading, ChatRoom
from .models.economy import Transaction, Vault
from .models.game import Game, GamePhase, GameRole, Order
from .models.map import Map
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
)

# db = DAL(app, pool_size=5, adapter_args={'uploads_in_blob': True})

celery = Celery("diplomatic", broker=app.config.worker.broker)
celery.conf.task_default_queue = "default"
celery.conf.task_serializer = "pickle"
celery.conf.accept_content = ["pickle"]
celery.conf.timezone = "UTC"
celery.conf.broker_transport_options = {"visibility_timeout": 60 * 60 * 24}
celery.conf.beat_schedule = parse_celery_cron(app.config.worker.get("cron", {}))


sessions = SessionManager.cookies("foobar")

# extensions
app.use_extension(RedisExtension)

from . import commands, tasks
