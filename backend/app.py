from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import requests
import json
import os
import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# CORS: allow localhost dev by default; tighten to your Firebase domain in prod
CORS(app, resources={r"*": {"origins": ["http://localhost:5173", "https://site-security-analyzer.web.app", "https://site-security-analyzer.firebaseapp.com"]}})

# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///site.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Security middleware
limiter = Limiter(get_remote_address, app=app, default_limits=["60 per minute"])  # global rate limit
Talisman(
    app,
    force_https=False,  # Cloud Run terminates TLS; set True if behind HTTPS only
    content_security_policy={
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'", "*"]
    },
)

HISTORY_FILE = "scans.json"

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

def save_scan(record):
    try:
        data = []
        if os.path.exists(HISTORY_FILE):
            data = json.load(open(HISTORY_FILE))
        data.append(record)
        json.dump(data, open(HISTORY_FILE, "w"), indent=2)
    except Exception as e:
        print("Failed to save:", e)


def init_db():
    """Create database tables if they don't exist.

    Flask 3 removed `before_first_request`. Create tables explicitly
    within an application context at startup so this works for the
    development server, gunicorn, and other WSGI servers.
    """
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print("DB init error:", e)


@app.route("/", methods=["GET"])
def root():
    """Root endpoint - API information."""
    return jsonify({
        "service": "Site Security Analyzer API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "scan": "POST /scan",
            "auth": {
                "signup": "POST /auth/signup",
                "login": "POST /auth/login"
            },
            "agent": "POST /agent/analyze",
            "billing": {
                "checkout": "POST /billing/create-checkout-session",
                "webhook": "POST /billing/webhook"
            }
        },
        "docs": "https://github.com/parthivvan/site-security-analyzer"
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Railway and other platforms."""
    return jsonify({"status": "healthy", "service": "site-security-analyzer"}), 200


@app.route("/agent/analyze", methods=["POST"])
@limiter.limit("15 per minute")
def agent_analyze():
    """Placeholder: Call Vertex AI Gemini to analyze a site report and return advice.
    Expected body: {"url": "..."}
    """
    body = request.get_json() or {}
    url = (body.get("url") or "").strip()
    if not url:
        return jsonify({"error": "url required"}), 400
    # TODO: integrate google-cloud-aiplatform Gemini call here.
    return jsonify({
        "url": url,
        "advice": [
            "Enable HSTS",
            "Set a strong Content-Security-Policy",
            "Add X-Content-Type-Options: nosniff",
        ],
        "note": "Gemini integration pending."
    })


@app.route("/billing/create-checkout-session", methods=["POST"])
@limiter.limit("10 per minute")
def billing_checkout():
    """Placeholder: Create Stripe Checkout Session and return url."""
    # TODO: integrate stripe.checkout.Session.create(...)
    return jsonify({"checkout_url": "https://stripe.example/placeholder"})


@app.route("/billing/webhook", methods=["POST"])
def billing_webhook():
    """Placeholder: validate Stripe webhook and update user entitlements."""
    # TODO: validate signature and process events
    return ("", 200)


@app.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "user already exists"}), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "signup successful"}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    payload = {
        "sub": user.id,
        "email": user.email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "iat": datetime.datetime.utcnow(),
    }
    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({"token": token, "user": {"id": user.id, "email": user.email}})


@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "no url provided"}), 400
    if not url.startswith("http"):
        url = "http://" + url

    try:
        r = requests.get(url, timeout=6)
        headers = dict(r.headers)
        report = {
            "url": url,
            "status_code": r.status_code,
            "https": url.startswith("https://"),
            "server_header": headers.get("Server"),
            "x_powered_by": headers.get("X-Powered-By"),
            "content_length": headers.get("Content-Length") or len(r.text),
            "hsts": "strict-transport-security" in [h.lower() for h in headers.keys()],
            "content_security_policy": "content-security-policy" in [h.lower() for h in headers.keys()],
            "x_frame_options": headers.get("X-Frame-Options"),
            "x_content_type_options": headers.get("X-Content-Type-Options"),
            "referrer_policy": headers.get("Referrer-Policy"),
        }

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    explanation = []

    if not report["https"]:
        explanation.append("No HTTPS, traffic can be intercepted.")
    else:
        explanation.append("Uses HTTPS.")

    if report["hsts"]:
        explanation.append("Implements HSTS (protects against protocol downgrade).")
    else:
        explanation.append("No HSTS header found.")

    if report["content_security_policy"]:
        explanation.append("Content Security Policy is present (helps block XSS).")
    else:
        explanation.append("No CSP header detected (may allow script injection).")

    if not report["x_frame_options"]:
        explanation.append("Missing X-Frame-Options (site can be iframed).")

    if not report["x_content_type_options"]:
        explanation.append("Missing X-Content-Type-Options (MIME sniffing possible).")

    if not report["referrer_policy"]:
        explanation.append("No Referrer-Policy (referrer data might leak).")

    if report["server_header"]:
        explanation.append(f"Server header reveals: {report['server_header']}.")

    explanation_text = " ".join(explanation)

    out = {"report": report, "explanation": explanation_text}
    save_scan({"url": url, "report": report})
    return jsonify(out)

if __name__ == "__main__":
    # Ensure DB is initialized when running the dev server
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)

# Also initialize DB at import time so WSGI servers (gunicorn/container
# deployments) create tables on startup. Calling init_db() at module
# import is safe because it uses app.app_context().
init_db()
