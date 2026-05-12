"""
Celery worker configuration and async scan tasks.

This module owns:
  - The Celery app instance.
  - The perform_security_scan task.
  - Scheduled cleanup tasks (old scans, expired tokens).
  - A standalone SQLAlchemy session for DB writes (avoids importing Flask app).
"""
import os
import json
import time
import datetime as _dt
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import redis
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import create_engine, text as _text
from sqlalchemy.orm import sessionmaker, scoped_session

from services.scanner import (
    create_safe_session,
    analyze_security_headers,
    analyze_cookies,
    analyze_page_content,
    check_dns_records,
    MAX_RESPONSE_SIZE,
    SCAN_TIMEOUT,
)
from services.scorer import build_flat_report, compute_score_from_flat_report, enrich_scan_result

# Inject Windows system certificates
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ── Celery app ────────────────────────────────────────────────────────

celery_app = Celery("scanner_tasks")
celery_app.conf.update(
    broker_url=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    result_backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=120,
    task_soft_time_limit=110,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# ── Redis cache (optional) ───────────────────────────────────────────

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
try:
    _redis = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
    _redis.ping()
    REDIS_CACHE_AVAILABLE = True
except Exception:
    _redis = None
    REDIS_CACHE_AVAILABLE = False

# ── Standalone SQLAlchemy session ────────────────────────────────────

_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///scanner.db")
if _DATABASE_URL.startswith("postgres://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Resolve relative SQLite paths
if _DATABASE_URL.startswith("sqlite:///") and not _DATABASE_URL.startswith("sqlite:////"):
    _db_filename = _DATABASE_URL[len("sqlite:///"):]
    if not os.path.isabs(_db_filename):
        _backend_dir = os.path.dirname(os.path.abspath(__file__))
        _backend_dir = os.path.dirname(_backend_dir)  # up from tasks/ to backend/
        _db_filename = os.path.join(_backend_dir, "instance", _db_filename)
        _DATABASE_URL = "sqlite:///" + _db_filename

_engine_kwargs: dict = {}
if _DATABASE_URL.startswith(("postgresql", "postgres")):
    _engine_kwargs = {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}
else:
    _engine_kwargs = {"connect_args": {"check_same_thread": False}}

_engine = create_engine(_DATABASE_URL, **_engine_kwargs)
_SessionFactory = scoped_session(sessionmaker(bind=_engine))


def _save_scan(
    user_id: int, url: str, domain: str, score: int, flat_report: dict, duration_ms: int
):
    session = _SessionFactory()
    try:
        session.execute(
            _text(
                "INSERT INTO scans (user_id, url, domain, score, report, scan_duration_ms, created_at)"
                " VALUES (:uid, :url, :domain, :score, :report, :dur, :ts)"
            ),
            {
                "uid": user_id,
                "url": url,
                "domain": domain,
                "score": score,
                "report": json.dumps(flat_report),
                "dur": duration_ms,
                "ts": _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f"),
            },
        )
        session.commit()
    except Exception as exc:
        session.rollback()
        raise exc
    finally:
        _SessionFactory.remove()


# ── Tasks ─────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="scanner.perform_security_scan")
def perform_security_scan(self, url: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Comprehensive security scan — runs in Celery worker."""
    start_time = time.time()
    parsed = urlparse(url)
    domain = parsed.hostname or ""

    try:
        self.update_state(state="PROGRESS", meta={"progress": 10, "stage": "Resolving DNS"})
        session = create_safe_session()

        self.update_state(state="PROGRESS", meta={"progress": 20, "stage": "Fetching headers"})

        with session.get(
            url, timeout=(5, SCAN_TIMEOUT), allow_redirects=True, stream=True
        ) as response:
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_RESPONSE_SIZE:
                return {"error": "Response too large", "url": url, "domain": domain}

            content = response.raw.read(MAX_RESPONSE_SIZE + 1, decode_content=True)
            if len(content) > MAX_RESPONSE_SIZE:
                return {"error": "Response too large", "url": url, "domain": domain}

            raw_headers = response.headers
            cookie_headers = getattr(response.raw, "headers", response.headers)
            final_url = response.url
            status_code = response.status_code

        self.update_state(state="PROGRESS", meta={"progress": 50, "stage": "Analyzing headers"})
        header_findings = analyze_security_headers(raw_headers, final_url)
        cookie_findings = analyze_cookies(cookie_headers)
        content_findings = analyze_page_content(content, final_url)

        self.update_state(state="PROGRESS", meta={"progress": 70, "stage": "Checking DNS"})
        dns_findings = check_dns_records(domain)

        all_findings = {
            "headers": header_findings,
            "cookies": cookie_findings,
            "dns": dns_findings,
            "content": content_findings,
        }

        flat_report = build_flat_report(header_findings, dns_findings, cookie_findings, content_findings)
        score = compute_score_from_flat_report(flat_report)

        self.update_state(state="PROGRESS", meta={"progress": 90, "stage": "Saving results"})

        result = {
            "url": url,
            "domain": domain,
            "findings": all_findings,
            "final_url": final_url,
            "status_code": status_code,
            "scan_duration_ms": int((time.time() - start_time) * 1000),
            "scanned_at": _dt.datetime.utcnow().isoformat(),
        }
        result = enrich_scan_result(result, flat_report, score)

        # Cache
        if REDIS_CACHE_AVAILABLE:
            _redis.setex(f"scan:{domain}", 3600, json.dumps(result))

        # DB
        if user_id:
            try:
                _save_scan(user_id, url, domain, score, flat_report, result["scan_duration_ms"])
            except Exception as db_err:
                result["db_error"] = str(db_err)

        return result

    except Exception as e:
        return {"error": f"Scan failed: {str(e)}", "url": url, "domain": domain}


@celery_app.task(name="scanner.cleanup_old_scans")
def cleanup_old_scans():
    session = _SessionFactory()
    try:
        cutoff = _dt.datetime.utcnow() - _dt.timedelta(days=90)
        result = session.execute(
            _text("DELETE FROM scans WHERE created_at < :cutoff"),
            {"cutoff": cutoff.strftime("%Y-%m-%d %H:%M:%S")},
        )
        session.commit()
        return f"Deleted {result.rowcount} old scans"
    except Exception:
        session.rollback()
        raise
    finally:
        _SessionFactory.remove()


@celery_app.task(name="scanner.cleanup_expired_tokens")
def cleanup_expired_tokens():
    session = _SessionFactory()
    try:
        now = _dt.datetime.utcnow()
        result = session.execute(
            _text("DELETE FROM refresh_tokens WHERE expires_at < :now"),
            {"now": now.strftime("%Y-%m-%d %H:%M:%S")},
        )
        session.commit()
        return f"Deleted {result.rowcount} expired tokens"
    except Exception:
        session.rollback()
        raise
    finally:
        _SessionFactory.remove()


# ── Scheduled tasks ──────────────────────────────────────────────────

celery_app.conf.beat_schedule = {
    "cleanup-old-scans": {
        "task": "scanner.cleanup_old_scans",
        "schedule": crontab(hour=2, minute=0),
    },
    "cleanup-expired-tokens": {
        "task": "scanner.cleanup_expired_tokens",
        "schedule": crontab(hour=3, minute=0),
    },
}
