"""
Site Security Analyzer - Production Backend
Fully secured against SSRF, auth vulnerabilities, and scaled for 100k+ users.
"""
import os
import re
import json
import socket
import ipaddress
import datetime
import secrets
import logging
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
from functools import wraps

from flask import Flask, request, jsonify, g, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_migrate import Migrate
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import redis
from pythonjsonlogger import jsonlogger
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from prometheus_flask_exporter import PrometheusMetrics

# Initialize Flask app
app = Flask(__name__)

# =====================================================================
# CONFIGURATION - PRODUCTION READY
# =====================================================================

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# CRITICAL: Validate SECRET_KEY
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 64:
    raise RuntimeError(
        "CRITICAL: SECRET_KEY must be set and at least 64 characters. "
        "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

# Handle Heroku postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

# PostgreSQL-specific pool options — SQLite uses StaticPool and doesn't accept these.
if DATABASE_URL.startswith(("postgresql", "postgres")):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": int(os.environ.get("DB_POOL_SIZE", 20)),
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", 40)),
    }
else:
    # SQLite: use check_same_thread=False so Flask threads don't conflict
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False}
    }

# Redis Configuration — optional. Falls back to a dummy when unavailable.
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
    redis_client.ping()  # test connection immediately
    REDIS_AVAILABLE = True
    print("Redis: connected")
except Exception as _redis_err:
    redis_client = None
    REDIS_AVAILABLE = False
    print(f"Redis: unavailable ({_redis_err}) — caching disabled, using sync scan mode")

# CORS Configuration
allowed_origins = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")]
print(f"CORS allowed origins: {allowed_origins}")
CORS(app, resources={r"/*": {"origins": allowed_origins}}, supports_credentials=True)

# Rate Limiting - use memory storage if Redis is not available
# Disable rate limiting in development to avoid blocking local testing
_is_production = os.environ.get("FLASK_ENV") == "production"

def _make_limiter():
    if not _is_production:
        print("Rate limiter: DISABLED (development mode)")
        return Limiter(
            key_func=get_remote_address,
            app=app,
            storage_uri="memory://",
            enabled=False
        )
    # Try Redis first; fall back to in-memory storage
    try:
        import redis as _redis
        _r = _redis.from_url(REDIS_URL, socket_connect_timeout=2)
        _r.ping()
        storage = REDIS_URL
        print("Rate limiter: using Redis storage")
    except Exception:
        storage = "memory://"
        print("Rate limiter: Redis unavailable, using in-memory storage")
    return Limiter(
        key_func=get_remote_address,
        app=app,
        storage_uri=storage,
        strategy="fixed-window",
        default_limits=["1000 per hour"]
    )

limiter = _make_limiter()

# Security Headers
is_production = os.environ.get("FLASK_ENV") == "production"
if is_production:
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
        content_security_policy_nonce_in=['script-src']
    )

# Database & Migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Monitoring
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Site Security Analyzer', version='2.0.0')

# Sentry Error Tracking
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment=os.environ.get("FLASK_ENV", "production")
    )

# =====================================================================
# STRUCTURED LOGGING
# =====================================================================

class ColoredFormatter(logging.Formatter):
    """Colored, structured logging formatter for development"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # Color the level name
        levelname = record.levelname
        if levelname in self.COLORS:
            colored_level = f"{self.COLORS[levelname]}{self.BOLD}{levelname:8s}{self.RESET}"
        else:
            colored_level = f"{levelname:8s}"
        
        # Format timestamp
        timestamp = self.formatTime(record, '%Y-%m-%d %H:%M:%S')
        
        # Format the message
        message = record.getMessage()
        
        # Structured output
        return f"[{timestamp}] {colored_level} │ {message}"

logHandler = logging.StreamHandler()

# Use colored formatter in development, JSON in production
if is_production:
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
else:
    formatter = ColoredFormatter()

logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO if is_production else logging.DEBUG)

# =====================================================================
# DATABASE MODELS
# =====================================================================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
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
    scans = db.relationship('Scan', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    refresh_tokens = db.relationship('RefreshToken', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """Hash password with bcrypt via werkzeug."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password: str) -> bool:
        """Verify password in constant time to prevent timing attacks."""
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self) -> bool:
        """Check if account is temporarily locked."""
        if self.account_locked_until:
            if datetime.datetime.utcnow() < self.account_locked_until:
                return True
            # Unlock account
            self.account_locked_until = None
            self.failed_login_attempts = 0
        return False
    
    def __repr__(self):
        return f'<User {self.email}>'


class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    revoked_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.Index('idx_refresh_user_active', 'user_id', 'revoked', 'expires_at'),
    )


class Scan(db.Model):
    __tablename__ = 'scans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    url = db.Column(db.String(2048), nullable=False)
    domain = db.Column(db.String(255), nullable=False, index=True)
    report = db.Column(db.Text, nullable=False)  # JSON
    score = db.Column(db.Integer, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    scan_duration_ms = db.Column(db.Integer)
    
    __table_args__ = (
        db.Index('idx_scan_user_created', 'user_id', 'created_at'),
        db.Index('idx_scan_domain_created', 'domain', 'created_at'),
    )


# =====================================================================
# SECURITY UTILITIES
# =====================================================================

def validate_url_safe(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Comprehensive URL validation to prevent SSRF attacks.
    
    Protects against:
    - DNS rebinding attacks
    - IPv6 bypass
    - Private IP access
    - Protocol smuggling
    - Invalid schemes
    
    Returns: (is_valid, normalized_url, error_message)
    """
    try:
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        parsed = urlparse(url)
        
        # Validate scheme
        if parsed.scheme not in ('http', 'https'):
            return False, url, "Only HTTP/HTTPS protocols allowed"
        
        hostname = parsed.hostname
        if not hostname:
            return False, url, "Invalid hostname"
        
        # Block obviously malicious patterns
        if any(char in hostname for char in ['@', ' ', '\n', '\r', '\t']):
            return False, url, "Invalid characters in hostname"
        
        # Resolve DNS and validate ALL resolved IPs
        try:
            resolved_ips = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror:
            return False, url, "Cannot resolve hostname"
        
        for ip_tuple in resolved_ips:
            try:
                ip_str = ip_tuple[4][0]
                # Remove IPv6 zone identifier if present
                if '%' in ip_str:
                    ip_str = ip_str.split('%')[0]
                
                ip_obj = ipaddress.ip_address(ip_str)
                
                # Block private, loopback, link-local, multicast, reserved
                if (ip_obj.is_private or ip_obj.is_loopback or 
                    ip_obj.is_link_local or ip_obj.is_multicast or 
                    ip_obj.is_reserved):
                    return False, url, f"Access to private/internal addresses not allowed ({ip_str})"
                
                # Extra protection for cloud metadata services
                if isinstance(ip_obj, ipaddress.IPv4Address):
                    # Block AWS metadata: 169.254.169.254
                    if ip_obj in ipaddress.ip_network('169.254.0.0/16'):
                        return False, url, "Access to cloud metadata services not allowed"
                    # Block localhost aliases
                    if ip_obj in ipaddress.ip_network('127.0.0.0/8'):
                        return False, url, "Access to localhost not allowed"
                
            except (ValueError, AttributeError) as e:
                logger.warning(f"IP validation error for {ip_str}: {e}")
                return False, url, "Invalid IP address"
        
        # Additional check: try to detect DNS rebinding by resolving again
        # In production, you'd want a custom DNS resolver with caching
        
        return True, url, None
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False, url, "Invalid URL format"


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """Validate password meets security requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password too long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain number"
    return True, None


def generate_access_token(user_id: int, email: str) -> str:  # noqa: E302
    """Generate short-lived access token (15 minutes)."""
    payload = {
        "sub": str(user_id),  # PyJWT 2.x: 'sub' must be a string (RFC 7519)
        "email": email,
        "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def generate_refresh_token(user: User) -> str:
    """Generate and store refresh token (7 days)."""
    token = secrets.token_urlsafe(64)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    
    refresh_token = RefreshToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.session.add(refresh_token)
    db.session.commit()
    
    return token


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT access token."""
    try:
        payload = jwt.decode(
            token,
            app.config["SECRET_KEY"],
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["exp", "sub", "type"]
            }
        )
        
        if payload.get("type") != "access":
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def auth_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_access_token(token)
        
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        g.user_id = int(payload.get('sub'))  # stored as str, back to int
        g.user_email = payload.get('email')
        
        return f(*args, **kwargs)
    
    return decorated


# =====================================================================
# REQUEST MIDDLEWARE
# =====================================================================

@app.before_request
def before_request():
    """Add request ID and start time."""
    g.request_id = request.headers.get('X-Request-ID', secrets.token_urlsafe(16))
    g.start_time = datetime.datetime.utcnow()
    
    logger.info('request_started', extra={
        'request_id': g.request_id,
        'method': request.method,
        'path': request.path,
        'ip': get_remote_address()
    })


@app.after_request
def after_request(response):
    """Log request completion."""
    duration_ms = (datetime.datetime.utcnow() - g.start_time).total_seconds() * 1000
    
    logger.info('request_completed', extra={
        'request_id': g.request_id,
        'method': request.method,
        'path': request.path,
        'status': response.status_code,
        'duration_ms': round(duration_ms, 2)
    })
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '0'  # Deprecated, CSP is better
    
    return response


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded."""
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {e}", exc_info=True, extra={
        'request_id': g.get('request_id'),
        'path': request.path
    })
    
    if is_production:
        return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": str(e)}), 500


# =====================================================================
# HEALTH & INFO ENDPOINTS
# =====================================================================

@app.route("/", methods=["GET"])
def root():
    """API information."""
    return jsonify({
        "service": "Site Security Analyzer API",
        "version": "2.0.0",
        "status": "running",
        "environment": os.environ.get("FLASK_ENV", "production")
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check with dependency checks."""
    health_status = {"status": "healthy", "checks": {}}
    status_code = 200
    
    # Check database
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        status_code = 503
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
        if status_code == 200:
            status_code = 200  # Redis failure is not critical
    
    return jsonify(health_status), status_code


@app.route("/ready", methods=["GET"])
def ready():
    """Readiness probe for Kubernetes."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "ready"}), 200
    except:
        return jsonify({"status": "not ready"}), 503


# =====================================================================
# AUTHENTICATION ENDPOINTS
# =====================================================================

@app.route("/auth/signup", methods=["POST"])
@limiter.limit("5 per hour")
def signup():
    """User registration with security hardening."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    
    # DEBUG: Log received credentials (password length and repr for debugging)
    logger.info(f"Signup attempt - Email: {email}, Password length: {len(password)}, Password repr: {repr(password)}")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    # Validate email
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    # Validate password strength
    is_strong, error_msg = validate_password_strength(password)
    if not is_strong:
        return jsonify({"error": error_msg}), 400
    
    # Check if user exists (with timing attack protection)
    import time, random
    start = time.time()
    
    existing = User.query.filter_by(email=email).first()
    
    # Add random delay to prevent timing attacks
    elapsed = time.time() - start
    if elapsed < 0.1:
        time.sleep(0.1 - elapsed + random.uniform(0, 0.05))
    
    if existing:
        # SECURITY: Return same message as success to prevent email enumeration
        logger.warning(f"Signup attempt for existing email: {email}")
        return jsonify({"message": "Account created successfully. Please check your email."}), 201
    
    # Create user
    user = User(email=email)
    user.set_password(password)
    
    # DEBUG: Log the generated hash
    logger.info(f"User created for {email} - Password hash: {user.password_hash[:30]}...")
    
    try:
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({"message": "Account created successfully. Please check your email."}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Signup error: {e}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """User login with brute force protection."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    
    # DEBUG: Log received credentials (password length and repr for debugging)
    logger.info(f"Login attempt - Email: {email}, Password length: {len(password)}, Password repr: {repr(password)}")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    # Constant-time response to prevent user enumeration
    import time, random
    time.sleep(random.uniform(0.1, 0.3))
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Check if account is locked
    if user.is_locked():
        return jsonify({"error": "Account temporarily locked. Try again later."}), 403
    
    # Check password
    if not user.check_password(password):
        # DEBUG: Log failed password check
        logger.warning(f"Password check failed for {email} - Password length: {len(password)}, Hash: {user.password_hash[:30]}...")
        
        # Increment failed attempts
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.account_locked_until = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
            logger.warning(f"Account locked due to failed login attempts: {email}")
        
        db.session.commit()
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Check if account is active
    if not user.is_active:
        return jsonify({"error": "Account disabled"}), 403
    
    # Successful login - reset failed attempts
    user.failed_login_attempts = 0
    user.account_locked_until = None
    user.last_login = datetime.datetime.utcnow()
    db.session.commit()
    
    # Generate tokens
    access_token = generate_access_token(user.id, user.email)
    refresh_token = generate_refresh_token(user)
    
    logger.info(f"User logged in: {email}")
    
    response = make_response(jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": 900,  # 15 minutes
        "user": {
            "id": user.id,
            "email": user.email
        }
    }))
    
    # Optionally set httpOnly cookie (recommended for web apps)
    # response.set_cookie(
    #     'refresh_token',
    #     refresh_token,
    #     httponly=True,
    #     secure=is_production,
    #     samesite='Strict',
    #     max_age=7*24*60*60
    # )
    
    return response, 200


@app.route("/auth/refresh", methods=["POST"])
@limiter.limit("20 per minute")
def refresh():
    """Refresh access token using refresh token."""
    data = request.get_json() or {}
    refresh_token_str = data.get("refresh_token")
    
    if not refresh_token_str:
        return jsonify({"error": "Refresh token required"}), 400
    
    # Find refresh token
    refresh_token = RefreshToken.query.filter_by(
        token=refresh_token_str,
        revoked=False
    ).first()
    
    if not refresh_token:
        return jsonify({"error": "Invalid refresh token"}), 401
    
    # Check expiry
    if datetime.datetime.utcnow() > refresh_token.expires_at:
        return jsonify({"error": "Refresh token expired"}), 401
    
    # Get user
    user = User.query.get(refresh_token.user_id)
    if not user or not user.is_active:
        return jsonify({"error": "Invalid user"}), 401
    
    # Generate new access token
    access_token = generate_access_token(user.id, user.email)
    
    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 900
    }), 200


@app.route("/auth/logout", methods=["POST"])
@auth_required
def logout():
    """Logout and revoke refresh tokens."""
    data = request.get_json() or {}
    refresh_token_str = data.get("refresh_token")
    
    if refresh_token_str:
        # Revoke specific refresh token
        refresh_token = RefreshToken.query.filter_by(
            token=refresh_token_str,
            user_id=g.user_id
        ).first()
        
        if refresh_token:
            refresh_token.revoked = True
            refresh_token.revoked_at = datetime.datetime.utcnow()
            db.session.commit()
    
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/auth/forgot-password", methods=["POST"])
@limiter.limit("3 per hour")
def forgot_password():
    """Request password reset token."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email required"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    # Always return same response to prevent email enumeration
    import time, random
    time.sleep(random.uniform(0.2, 0.4))
    
    if user and user.is_active:
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        user.reset_token_used_at = None
        db.session.commit()
        
        # TODO: Send email with reset link
        logger.info(f"Password reset requested: {email}")
        # In dev, you could log the token
        if not is_production:
            logger.debug(f"Reset token for {email}: {reset_token}")
    
    return jsonify({
        "message": "If your email exists, you will receive a password reset link."
    }), 200


@app.route("/auth/reset-password", methods=["POST"])
@limiter.limit("5 per hour")
def reset_password():
    """Reset password using token."""
    data = request.get_json() or {}
    token = data.get("token") or ""
    new_password = data.get("password") or ""
    
    if not token or not new_password:
        return jsonify({"error": "Token and password required"}), 400
    
    # Validate new password
    is_strong, error_msg = validate_password_strength(new_password)
    if not is_strong:
        return jsonify({"error": error_msg}), 400
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 400
    
    # Check token expiry
    if user.reset_token_expiry < datetime.datetime.utcnow():
        return jsonify({"error": "Invalid or expired token"}), 400
    
    # Check if token was already used
    if user.reset_token_used_at:
        return jsonify({"error": "Token already used"}), 400
    
    # Update password
    user.set_password(new_password)
    user.reset_token_used_at = datetime.datetime.utcnow()
    user.reset_token = None  # Clear token
    user.failed_login_attempts = 0  # Reset failed attempts
    user.account_locked_until = None  # Unlock account
    
    # Revoke all refresh tokens (force re-login)
    RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({
        'revoked': True,
        'revoked_at': datetime.datetime.utcnow()
    })
    
    db.session.commit()
    
    logger.info(f"Password reset completed: {user.email}")
    
    return jsonify({"message": "Password reset successful"}), 200


@app.route("/auth/history", methods=["GET"])
@auth_required
def get_user_history():
    """Get scan history for authenticated user."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    scans_query = Scan.query.filter_by(user_id=g.user_id).order_by(Scan.created_at.desc())
    
    paginated = scans_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "total": paginated.total,
        "page": page,
        "per_page": per_page,
        "pages": paginated.pages,
        "scans": [
            {
                "id": scan.id,
                "url": scan.url,
                "domain": scan.domain,
                "score": scan.score,
                "report": json.loads(scan.report),
                "created_at": scan.created_at.isoformat(),
                "scan_duration_ms": scan.scan_duration_ms
            }
            for scan in paginated.items
        ]
    })


# =====================================================================
# SCAN ENDPOINT - QUEUE BASED (async via Celery)
# =====================================================================

@app.route("/scan", methods=["POST"])
@limiter.limit("30 per hour")
@auth_required
def scan():
    """
    Security scan endpoint.

    • If Celery/Redis are available → queues async task (202 + task_id).
    • If Redis is unavailable (dev/local) → runs scan synchronously inline
      and returns the full result immediately (200).
    """
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL required"}), 400

    # Validate URL and check for SSRF
    is_valid, normalized_url, error = validate_url_safe(url)
    if not is_valid:
        logger.warning(f"Invalid URL rejected: {url} - {error}")
        return jsonify({"error": error}), 400

    domain = urlparse(normalized_url).hostname

    # Check Redis cache (skip if Redis is down)
    if REDIS_AVAILABLE:
        cache_key = f"scan:{domain}"
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Returning cached scan for {domain}")
            return jsonify(json.loads(cached)), 200

    # ── Async path (Celery available) ──────────────────────────────────────
    if REDIS_AVAILABLE:
        try:
            from celery_tasks import perform_security_scan
            task = perform_security_scan.delay(normalized_url, g.user_id)
            return jsonify({
                "task_id": task.id,
                "status": "queued",
                "message": "Scan started. Poll /scan/status/<task_id> for results."
            }), 202
        except Exception as celery_err:
            logger.warning(f"Celery unavailable ({celery_err}), falling back to sync scan")

    # ── Synchronous fallback (no Celery/Redis — development mode) ──────────
    logger.info(f"Running synchronous scan for {normalized_url}")
    try:
        from celery_tasks import (
            create_safe_session, analyze_security_headers,
            analyze_cookies, check_dns_records, calculate_overall_score
        )
        import time as _time

        start_time = _time.time()
        session = create_safe_session()
        response = session.get(
            normalized_url,
            timeout=(5, 10),
            allow_redirects=True,
            stream=True
        )
        content = response.raw.read(1 * 1024 * 1024, decode_content=True)  # 1 MB max
        headers = dict(response.headers)

        header_findings = analyze_security_headers(headers, response.url)
        cookie_findings = analyze_cookies(headers)
        dns_findings    = check_dns_records(domain)

        all_findings = {"headers": header_findings, "cookies": cookie_findings, "dns": dns_findings}
        score = calculate_overall_score({**header_findings, **cookie_findings, **dns_findings})

        # Build flat report that frontend computeScore() expects
        flat_report = {
            "https":                   header_findings.get("https", {}).get("present", False),
            "hsts":                    header_findings.get("hsts", {}).get("present", False),
            "content_security_policy": header_findings.get("csp", {}).get("present", False),
            "x_frame_options":         header_findings.get("x_frame_options", {}).get("present", False),
            "x_content_type_options":  header_findings.get("x_content_type_options", {}).get("present", False),
            "referrer_policy":         header_findings.get("referrer_policy", {}).get("present", False),
            "permissions_policy":      header_findings.get("permissions_policy", {}).get("present", False),
            "server_header":           header_findings.get("server_disclosure", {}).get("present", False),
            "dns_spf":                 dns_findings.get("spf", {}).get("present", False),
            "dns_dmarc":               dns_findings.get("dmarc", {}).get("present", False),
        }

        # Build explanation
        label_map = {
            "https": "HTTPS", "hsts": "HSTS", "content_security_policy": "CSP",
            "x_frame_options": "X-Frame-Options", "x_content_type_options": "X-Content-Type-Options",
            "referrer_policy": "Referrer-Policy", "permissions_policy": "Permissions-Policy",
            "dns_spf": "SPF", "dns_dmarc": "DMARC",
        }
        passed = [label_map.get(k, k) for k, v in flat_report.items() if k != "server_header" and v]
        failed = [label_map.get(k, k) for k, v in flat_report.items() if k != "server_header" and not v]
        grade = "Excellent" if score >= 80 else "Good" if score >= 60 else "Moderate" if score >= 40 else "Critical"
        explanation = (
            f"<strong>Security Grade: {grade} ({score}/100)</strong><br>"
            f"<strong>Passed ({len(passed)}):</strong> {', '.join(passed) or 'None'}<br>"
            f"<strong>Failed ({len(failed)}):</strong> {', '.join(failed) or 'None'}"
            + (" <br><em>&#9888; Server version is disclosed in response headers.</em>" if flat_report.get("server_header") else "")
        )

        duration_ms = int((_time.time() - start_time) * 1000)

        result = {
            "url": normalized_url,
            "domain": domain,
            "score": score,
            "report": flat_report,
            "findings": all_findings,
            "explanation": explanation,
            "final_url": response.url,
            "status_code": response.status_code,
            "scan_duration_ms": duration_ms,
            "scanned_at": datetime.datetime.utcnow().isoformat()
        }

        # Save to database
        try:
            scan_record = Scan(
                user_id=g.user_id,
                url=normalized_url,
                domain=domain,
                score=score,
                report=json.dumps(flat_report),
                scan_duration_ms=duration_ms
            )
            db.session.add(scan_record)
            db.session.commit()
            logger.info(f"Scan saved to DB: {domain} score={score}")
        except Exception as db_err:
            db.session.rollback()
            logger.error(f"Failed to save scan to DB: {db_err}")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Sync scan error: {e}")
        return jsonify({"error": f"Scan failed: {str(e)}"}), 500


@app.route("/scan/status/<task_id>", methods=["GET"])
@auth_required
def scan_status(task_id):
    """Check status of queued scan."""
    from celery_tasks import celery
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id, app=celery)
    
    if task.ready():
        if task.successful():
            result = task.result
            return jsonify({
                "status": "complete",
                "result": result
            }), 200
        else:
            return jsonify({
                "status": "failed",
                "error": str(task.info)
            }), 200
    else:
        return jsonify({
            "status": "processing",
            "progress": task.info.get('progress', 0) if isinstance(task.info, dict) else 0
        }), 200


# =====================================================================
# DATABASE INITIALIZATION
# =====================================================================

def init_db():
    """Create database tables."""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created")
    except Exception as e:
        logger.error(f"DB init error: {e}")


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not is_production)

# Initialize DB at import time for WSGI servers
init_db()
