"""Authentication routes — signup, login, refresh, logout, password reset, history."""
import datetime
import json
import logging

from flask import Blueprint, request, jsonify, g, make_response
import jwt as pyjwt
from werkzeug.security import check_password_hash

from config import Config
from extensions import db, limiter
from models.user import User, RefreshToken
from models.scan import Scan
from utils.helpers import (
    utcnow,
    utcnow_aware,
    hash_token,
    email_fingerprint,
    generate_secure_token,
    DUMMY_HASH,
)
from utils.validators import validate_email, validate_password_strength

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ── Token generation ──────────────────────────────────────────────────

def generate_access_token(user_id: int, email: str) -> str:
    """Generate short-lived access token (15 minutes)."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": utcnow_aware() + datetime.timedelta(minutes=15),
        "iat": utcnow_aware(),
    }
    return pyjwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")


def generate_refresh_token(user: User) -> str:
    """Generate and store a hashed refresh token (7 days)."""
    token = generate_secure_token(64)
    expires_at = utcnow() + datetime.timedelta(days=7)

    rt = RefreshToken(
        user_id=user.id,
        token=hash_token(token),
        expires_at=expires_at,
    )
    db.session.add(rt)
    db.session.commit()
    return token


def verify_access_token(token: str):
    """Verify JWT access token. Returns payload dict or None."""
    try:
        payload = pyjwt.decode(
            token,
            Config.SECRET_KEY,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["exp", "sub", "type"],
            },
        )
        if payload.get("type") != "access":
            return None
        return payload
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


# ── Decorator ─────────────────────────────────────────────────────────

def auth_required(f):
    """Decorator to require authentication."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(" ")[1]
        payload = verify_access_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.user_id = int(payload.get("sub"))
        g.user_email = payload.get("email")
        return f(*args, **kwargs)

    return decorated


# ── Endpoints ─────────────────────────────────────────────────────────

@auth_bp.route("/signup", methods=["POST"])
@limiter.limit("5 per hour")
def signup():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    logger.info("Signup attempt for email_fp: %s", email_fingerprint(email))

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    is_strong, error_msg = validate_password_strength(password)
    if not is_strong:
        return jsonify({"error": error_msg}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        logger.warning("Signup attempt for existing email_fp: %s", email_fingerprint(email))
        return jsonify({"error": "An account with this email already exists. Please log in."}), 409

    user = User(email=email)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        logger.info("New user registered: %s", email_fingerprint(email))
        return jsonify({"message": "Account created successfully. Please check your email."}), 201
    except Exception as e:
        db.session.rollback()
        logger.error("Signup error: %s", e)
        return jsonify({"error": "Registration failed"}), 500


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    logger.info("Login attempt for email_fp: %s", email_fingerprint(email))

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        check_password_hash(DUMMY_HASH, password)
        return jsonify({"error": "Invalid credentials"}), 401

    if user.is_locked():
        return jsonify({"error": "Account temporarily locked. Try again later."}), 403

    if not user.check_password(password):
        logger.warning("Password check failed for %s", email_fingerprint(email))
        lock_until = utcnow() + datetime.timedelta(minutes=30)
        db.session.execute(
            db.text(
                "UPDATE users SET failed_login_attempts = failed_login_attempts + 1, "
                "account_locked_until = CASE WHEN failed_login_attempts + 1 >= 5 THEN :lock_until ELSE account_locked_until END "
                "WHERE id = :uid"
            ),
            {"lock_until": lock_until, "uid": user.id},
        )
        db.session.commit()
        db.session.refresh(user)
        if user.failed_login_attempts >= 5:
            logger.warning("Account locked: %s", email_fingerprint(email))
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"error": "Account disabled"}), 403

    user.failed_login_attempts = 0
    user.account_locked_until = None
    user.last_login = utcnow()
    db.session.commit()

    access_token = generate_access_token(user.id, user.email)
    refresh_token = generate_refresh_token(user)

    logger.info("User logged in: %s", email_fingerprint(email))

    response = make_response(
        jsonify(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 900,
                "user": {"id": user.id, "email": user.email},
            }
        )
    )
    return response, 200


@auth_bp.route("/refresh", methods=["POST"])
@limiter.limit("20 per minute")
def refresh():
    data = request.get_json() or {}
    refresh_token_str = data.get("refresh_token")
    if not refresh_token_str:
        return jsonify({"error": "Refresh token required"}), 400

    rt = RefreshToken.query.filter_by(
        token=hash_token(refresh_token_str), revoked=False
    ).first()

    if not rt:
        return jsonify({"error": "Invalid refresh token"}), 401
    if utcnow() > rt.expires_at:
        return jsonify({"error": "Refresh token expired"}), 401

    user = db.session.get(User, rt.user_id)
    if not user or not user.is_active:
        return jsonify({"error": "Invalid user"}), 401

    access_token = generate_access_token(user.id, user.email)
    return jsonify({"access_token": access_token, "token_type": "Bearer", "expires_in": 900}), 200


@auth_bp.route("/logout", methods=["POST"])
@auth_required
def logout():
    data = request.get_json() or {}
    refresh_token_str = data.get("refresh_token")
    if refresh_token_str:
        rt = RefreshToken.query.filter_by(
            token=hash_token(refresh_token_str), user_id=g.user_id
        ).first()
        if rt:
            rt.revoked = True
            rt.revoked_at = utcnow()
            db.session.commit()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("3 per hour")
def forgot_password():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email required"}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.is_active:
        reset_token = generate_secure_token(32)
        user.reset_token = hash_token(reset_token)
        user.reset_token_expiry = utcnow() + datetime.timedelta(hours=1)
        user.reset_token_used_at = None
        db.session.commit()

        logger.info("Password reset requested: %s", email_fingerprint(email))
        if not Config.IS_PRODUCTION:
            logger.debug("Reset token for %s: %s", email, reset_token)

    return jsonify({"message": "If your email exists, you will receive a password reset link."}), 200


@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("5 per hour")
def reset_password():
    data = request.get_json() or {}
    token = data.get("token") or ""
    new_password = data.get("password") or ""

    if not token or not new_password:
        return jsonify({"error": "Token and password required"}), 400

    is_strong, error_msg = validate_password_strength(new_password)
    if not is_strong:
        return jsonify({"error": error_msg}), 400

    user = User.query.filter_by(reset_token=hash_token(token)).first()
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 400
    if user.reset_token_expiry < utcnow():
        return jsonify({"error": "Invalid or expired token"}), 400
    if user.reset_token_used_at:
        return jsonify({"error": "Token already used"}), 400

    user.set_password(new_password)
    user.reset_token_used_at = utcnow()
    user.reset_token = None
    user.failed_login_attempts = 0
    user.account_locked_until = None

    RefreshToken.query.filter_by(user_id=user.id, revoked=False).update(
        {"revoked": True, "revoked_at": utcnow()}
    )
    db.session.commit()

    logger.info("Password reset completed: %s", email_fingerprint(user.email))
    return jsonify({"message": "Password reset successful"}), 200


@auth_bp.route("/history", methods=["GET"])
@auth_required
def get_user_history():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 100)

    paginated = (
        Scan.query.filter_by(user_id=g.user_id)
        .order_by(Scan.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            "total": paginated.total,
            "page": page,
            "per_page": per_page,
            "pages": paginated.pages,
            "scans": [
                {
                    "id": s.id,
                    "url": s.url,
                    "domain": s.domain,
                    "score": s.score,
                    "report": json.loads(s.report),
                    "created_at": s.created_at.isoformat(),
                    "scan_duration_ms": s.scan_duration_ms,
                }
                for s in paginated.items
            ],
        }
    )
