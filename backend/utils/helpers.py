"""Low-level helpers shared across the entire backend."""
import datetime
import hashlib
import secrets

from werkzeug.security import generate_password_hash


# ── Datetime helpers ──────────────────────────────────────────────────

def utcnow() -> datetime.datetime:
    """Naive UTC datetime for DB columns; compatible with SQLite and PostgreSQL."""
    return datetime.datetime.utcnow()


def utcnow_aware() -> datetime.datetime:
    """Timezone-aware UTC datetime for JWT payloads only."""
    return datetime.datetime.now(datetime.timezone.utc)


# ── Token helpers ─────────────────────────────────────────────────────

def hash_token(token: str) -> str:
    """One-way SHA-256 hash for refresh/reset token storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def email_fingerprint(email: str) -> str:
    """Return a short hash of the email for safe logging (no PII)."""
    return hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]


def generate_secure_token(nbytes: int = 64) -> str:
    """Return a cryptographically-random URL-safe token."""
    return secrets.token_urlsafe(nbytes)


# ── Timing-attack normalization ───────────────────────────────────────
# A dummy bcrypt hash used when a login is attempted for a non-existent
# email, so the response time is identical to a real user lookup.
DUMMY_HASH = generate_password_hash("dummy-timing-normalization-value-do-not-use")
