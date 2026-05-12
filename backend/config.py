"""
Centralised configuration — every env-specific value lives here.

Usage:
    from config import Config
    app.config.from_object(Config)
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Secrets ────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "") or SECRET_KEY

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    # Handle Heroku postgres:// → postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    # Resolve relative SQLite paths to absolute (prevents Flask instance_path doubling)
    if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
        _db_file = DATABASE_URL[len("sqlite:///"):]
        if not os.path.isabs(_db_file):
            _backend_dir = os.path.dirname(os.path.abspath(__file__))
            _db_file = os.path.join(_backend_dir, "instance", _db_file)
            os.makedirs(os.path.dirname(_db_file), exist_ok=True)
            DATABASE_URL = "sqlite:///" + _db_file
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def engine_options() -> dict:
        """Return SQLALCHEMY_ENGINE_OPTIONS appropriate for the DB backend."""
        url = Config.SQLALCHEMY_DATABASE_URI
        if url.startswith(("postgresql", "postgres")):
            return {
                "pool_size": int(os.environ.get("DB_POOL_SIZE", 20)),
                "pool_recycle": 3600,
                "pool_pre_ping": True,
                "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", 40)),
            }
        # SQLite
        return {"connect_args": {"check_same_thread": False}}

    # ── Redis ──────────────────────────────────────────────────────────
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # ── Celery ─────────────────────────────────────────────────────────
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # ── CORS ───────────────────────────────────────────────────────────
    ALLOWED_ORIGINS = [
        o.strip()
        for o in os.environ.get(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
    ]

    # ── Runtime ────────────────────────────────────────────────────────
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    IS_PRODUCTION = FLASK_ENV == "production"
    PORT = int(os.environ.get("PORT", 5000))

    # ── Scanner defaults ───────────────────────────────────────────────
    SCAN_TIMEOUT = int(os.environ.get("SCAN_TIMEOUT_SECONDS", 30))
    MAX_RESPONSE_SIZE = int(os.environ.get("MAX_RESPONSE_SIZE_MB", 10)) * 1024 * 1024
    MAX_REDIRECTS = int(os.environ.get("MAX_REDIRECTS", 3))
    USE_CELERY = os.environ.get("USE_CELERY", "false").lower() == "true"

    # ── Sentry ─────────────────────────────────────────────────────────
    SENTRY_DSN = os.environ.get("SENTRY_DSN", "")

    # ── Validation ─────────────────────────────────────────────────────
    @classmethod
    def validate(cls):
        """Raise early if critical config is missing."""
        if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 64:
            raise RuntimeError(
                "CRITICAL: SECRET_KEY must be set and at least 64 characters. "
                'Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError("DATABASE_URL must be set")
