"""
Shared extension instances — imported by models, routes, and the app factory.

This module exists so that db / limiter / redis_client can be imported
without importing the Flask app itself, breaking circular imports.
"""
import logging
import redis
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ── Database ───────────────────────────────────────────────────────────
db = SQLAlchemy()
migrate = Migrate()

# ── Rate Limiter (configured later in app factory) ─────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── Prometheus (initialised in app factory) ────────────────────────────
metrics = None

# ── Redis ──────────────────────────────────────────────────────────────
redis_client = None
REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


def init_redis(redis_url: str):
    """Try to connect to Redis; set module-level globals."""
    global redis_client, REDIS_AVAILABLE
    try:
        redis_client = redis.from_url(
            redis_url, decode_responses=True, socket_connect_timeout=2
        )
        redis_client.ping()
        REDIS_AVAILABLE = True
        logger.info("Redis: connected")
    except Exception as err:
        redis_client = None
        REDIS_AVAILABLE = False
        logger.info("Redis: unavailable (%s) — caching disabled, using sync scan mode", err)
