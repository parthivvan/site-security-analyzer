"""
Site Security Analyzer — App Factory

This is the only file that creates the Flask app. It:
  1. Validates configuration.
  2. Initialises extensions (DB, Redis, limiter, Sentry, Talisman).
  3. Registers Blueprints (auth, scans).
  4. Sets up middleware (request logging, security headers, error handlers).
  5. Creates database tables and runs one-time migrations.

Usage:
    python app.py            → dev server
    gunicorn app:app          → production WSGI
"""
import os
import json
import logging
import secrets
import traceback
from contextlib import suppress

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_talisman import Talisman
from flask_limiter.util import get_remote_address
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from pythonjsonlogger import jsonlogger
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from prometheus_flask_exporter import PrometheusMetrics

from config import Config
from extensions import db, migrate, limiter, init_redis
from utils.helpers import utcnow


# ── Logging ──────────────────────────────────────────────────────────

class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record):
        level = record.levelname
        colored = f"{self.COLORS.get(level, '')}{self.BOLD}{level:8s}{self.RESET}"
        ts = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        return f"[{ts}] {colored} │ {record.getMessage()}"


def _setup_logging(is_production: bool):
    handler = logging.StreamHandler()
    if is_production:
        handler.setFormatter(
            jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    else:
        handler.setFormatter(ColoredFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO if is_production else logging.DEBUG)


logger = logging.getLogger(__name__)


# ── App Factory ──────────────────────────────────────────────────────

def create_app() -> Flask:
    """Application factory — creates and configures the Flask app."""
    Config.validate()

    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = Config.engine_options()

    is_prod = Config.IS_PRODUCTION

    # Logging
    _setup_logging(is_prod)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Rate Limiter
    if not is_prod:
        limiter.init_app(app)
        limiter.enabled = False
        logger.info("Rate limiter: DISABLED (development mode)")
    else:
        try:
            import redis as _redis

            _r = _redis.from_url(Config.REDIS_URL, socket_connect_timeout=2)
            _r.ping()
            storage = Config.REDIS_URL
            logger.info("Rate limiter: using Redis storage")
        except Exception:
            storage = "memory://"
            logger.info("Rate limiter: Redis unavailable, using in-memory storage")
        app.config["RATELIMIT_STORAGE_URI"] = storage
        app.config["RATELIMIT_STRATEGY"] = "fixed-window"
        app.config["RATELIMIT_DEFAULT"] = "1000 per hour"
        limiter.init_app(app)

    # Redis
    init_redis(Config.REDIS_URL)

    # CORS
    CORS(
        app,
        resources={r"/*": {"origins": Config.ALLOWED_ORIGINS}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Talisman (production only)
    if is_prod:
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            content_security_policy={
                "default-src": ["'self'"],
                "script-src": ["'self'"],
                "style-src": ["'self'", "'unsafe-inline'"],
                "img-src": ["'self'", "data:", "https:"],
                "connect-src": ["'self'"],
                "frame-ancestors": ["'none'"],
            },
            content_security_policy_nonce_in=["script-src"],
        )

    # Prometheus
    metrics = PrometheusMetrics(app)
    metrics.info("app_info", "Site Security Analyzer", version="2.0.0")

    # Sentry
    if Config.SENTRY_DSN:
        sentry_sdk.init(
            dsn=Config.SENTRY_DSN,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
            environment=Config.FLASK_ENV,
        )

    # ── Import models so SQLAlchemy sees them ─────────────────────────
    import models  # noqa: F401

    # ── Register Blueprints ───────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.scans import scans_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(scans_bp)

    # ── Health / Info endpoints ───────────────────────────────────────

    @app.route("/", methods=["GET"])
    def root():
        return jsonify(
            {
                "service": "Site Security Analyzer API",
                "version": "2.0.0",
                "status": "running",
                "environment": Config.FLASK_ENV,
            }
        ), 200

    @app.route("/health", methods=["GET"])
    def health():
        from extensions import redis_client

        health_status = {"status": "healthy", "checks": {}}
        code = 200

        try:
            db.session.execute(db.text("SELECT 1"))
            health_status["checks"]["database"] = "ok"
        except Exception as e:
            health_status["checks"]["database"] = f"error: {e}"
            health_status["status"] = "unhealthy"
            code = 503

        if redis_client is None:
            health_status["checks"]["redis"] = "unavailable (not configured)"
        else:
            try:
                redis_client.ping()
                health_status["checks"]["redis"] = "ok"
            except Exception as e:
                health_status["checks"]["redis"] = f"error: {e}"
                health_status["status"] = "degraded"

        return jsonify(health_status), code

    @app.route("/ready", methods=["GET"])
    def ready():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify({"status": "ready"}), 200
        except Exception:
            return jsonify({"status": "not ready"}), 503

    # ── Middleware ─────────────────────────────────────────────────────

    @app.before_request
    def before_request():
        g.request_id = request.headers.get("X-Request-ID", secrets.token_urlsafe(16))
        g.start_time = utcnow()

    @app.after_request
    def after_request(response):
        start = getattr(g, "start_time", utcnow())
        duration_ms = (utcnow() - start).total_seconds() * 1000
        logger.info(
            "request_completed",
            extra={
                "request_id": getattr(g, "request_id", "-"),
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        return response

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error("Unhandled exception: %s", e, exc_info=True)
        if isinstance(e, OperationalError):
            return jsonify(
                {
                    "error": "Database schema is not initialized. Restart the backend or run migrations.",
                    "code": "database_schema_missing",
                }
            ), 500
        if is_prod:
            return jsonify({"error": "Internal server error"}), 500
        return jsonify(
            {"error": str(e), "type": type(e).__name__, "traceback": traceback.format_exc()}
        ), 500

    return app


def _init_db(app: Flask):
    """Create tables, verify schema, and invalidate legacy plaintext tokens."""
    try:
        with app.app_context():
            db.create_all()

            existing_tables = set(inspect(db.engine).get_table_names())
            required = {"users", "refresh_tokens", "scans"}
            missing = required - existing_tables

            if missing:
                logger.warning("Missing tables after create_all: %s", sorted(missing))
            else:
                logger.info("Database schema ready")

            # Revoke legacy plaintext refresh tokens
            if "refresh_tokens" in existing_tables:
                with suppress(Exception):
                    result = db.session.execute(
                        db.text(
                            "UPDATE refresh_tokens SET revoked = 1 "
                            "WHERE revoked = 0 AND length(token) != 64"
                        )
                    )
                    db.session.commit()
                    if result.rowcount:
                        logger.info("Revoked %d legacy plaintext refresh tokens", result.rowcount)
    except Exception as e:
        logger.error("DB init error: %s", e)


# ── Module-level app instance (for WSGI / dev server) ────────────────

app = create_app()

# Only init the real DB when running as a server, not when tests import this module.
# Tests override SQLALCHEMY_DATABASE_URI to :memory: in setUp() and call db.create_all() themselves.
if not app.config.get("TESTING"):
    _init_db(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=not Config.IS_PRODUCTION)
