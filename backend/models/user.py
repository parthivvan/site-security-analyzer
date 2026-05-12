"""User and RefreshToken ORM models."""
from extensions import db
from utils.helpers import utcnow
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Password reset
    reset_token = db.Column(db.String(100), unique=True, index=True)
    reset_token_expiry = db.Column(db.DateTime)
    reset_token_used_at = db.Column(db.DateTime)

    # Rate limiting
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)

    # Relationships
    scans = db.relationship(
        "Scan", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    refresh_tokens = db.relationship(
        "RefreshToken", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    # ── password helpers ──────────────────────────────────────────────
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256"
        )

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ── lockout ───────────────────────────────────────────────────────
    def is_locked(self) -> bool:
        if self.account_locked_until:
            if utcnow() < self.account_locked_until:
                return True
            self.account_locked_until = None
            self.failed_login_attempts = 0
        return False

    def __repr__(self):
        return f"<User {self.email}>"


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    revoked_at = db.Column(db.DateTime)

    __table_args__ = (
        db.Index("idx_refresh_user_active", "user_id", "revoked", "expires_at"),
    )
