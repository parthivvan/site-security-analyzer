# Site Security Analyzer — Full Repo Walkthrough (Backend + Frontend + Extension + Infra)

This document is an **end-to-end deep dive** of the repo: what each folder/file is for, how the main logic works at runtime, how auth + scanning + history fit together, and which parts are “real runtime” vs “one-off scripts” vs “stale/outdated artifacts”.

> Key idea: the **truth of runtime behavior** is primarily in:
> - `backend/app.py` (Flask API + auth + scan orchestration + SSRF defenses)
> - `backend/celery_tasks.py` (safe HTTP client + scan work + async Celery task)
> - `backend/core/report_builder.py` (turns raw findings into the stable report contract consumed by UI)
> - `frontend/src/api.js` (token manager + refresh behavior)
> - `frontend/src/SiteSecurityAnalyzer.jsx` (scan UI + polling for async scans)
> - `extension/popup.js` (extension login + scan + poll)

## Table of Contents

1. Repo map
2. Local run (Windows)
3. End-to-end runtime flows
4. Backend deep dive
5. Frontend deep dive
6. Browser extension deep dive
7. Infra / deployment configs
8. One-off scripts (root)
9. Known inconsistencies / stale docs
10. Optional cleanup plan
11. Smoke test checklist

---

## 0) Repo map (what exists)

Top-level folders and their purpose:

- `backend/` — Flask API, scanning logic, async worker support, DB persistence, tests.
- `frontend/` — React + Vite UI (auth pages + analyzer page + history + learn).
- `extension/` — Chrome MV3 extension (popup UI that calls backend).
- `nginx/` — Nginx reverse proxy config (mostly for “big stack” deployment).
- `monitoring/` — Prometheus scrape config (Grafana provisioning folders referenced but may be missing).
- `instance/` — runtime artifacts (SQLite DBs, etc.) depending on how you run.

Top-level files (selected):

- `docker-compose.yml` — “production stack” compose (Postgres + Redis + backend + Celery + Prometheus + Grafana + Nginx), but currently has **port/module mismatches** with the Dockerfiles/start scripts.
- `Dockerfile` — root dockerfile (intended for Railway) that copies `backend/` into the container.
- `cloudbuild.yaml`, `render.yaml`, `railway.json`, `vercel.json`, `firebase.json` — deployment descriptors for different platforms.
- `README.md`, `DEPLOYMENT_GUIDE.md`, `PRODUCTION_DEPLOYMENT.md`, `SECURITY_FIXES.md`, `COMPLETE.md` — documentation (some is stale / references files not present).

Also present: a handful of one-off Python scripts at repo root (`cleanup_ui.py`, `refactor_ui.py`, etc.) used for UI mass-edits and patching.

---

## 1) How to run locally on Windows (recommended dev path)

### 1.1 Backend (Flask) — minimal dev setup

**Backend hard-requirements at startup (enforced in code):**
- `SECRET_KEY` must exist and be **≥ 64 characters**.
- `DATABASE_URL` must exist.

Recommended local values:
- `DATABASE_URL=sqlite:///instance/scanner.db` (creates `backend/instance/scanner.db` if you run from `backend/`)

Common environment variables used by the backend:

- **Required**
  - `SECRET_KEY` — must be ≥ 64 chars
  - `DATABASE_URL` — SQLAlchemy URL (SQLite or Postgres)
- **Optional runtime toggles**
  - `FLASK_ENV` — set to `production` to enable stricter hardening/limits
  - `PORT` — server port (defaults to 5000 when running `python app.py`)
  - `ALLOWED_ORIGINS` — comma-separated list for CORS
  - `REDIS_URL` — enables Redis caching + distributed rate-limit storage (if configured)
  - `USE_CELERY` — if `true`, backend tries queue-mode scans
  - `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` — Celery broker/result
  - `SENTRY_DSN` — enables error reporting to Sentry

**PowerShell (run from repo root):**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Required env vars
$env:FLASK_ENV = "development"
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(64))")
$env:DATABASE_URL = "sqlite:///instance/scanner.db"

python app.py
```

Expected:
- Backend starts on `http://127.0.0.1:5000`
- It will create tables at startup via `init_db()`.

### 1.2 Frontend (React + Vite)

PowerShell (from repo root):

```powershell
cd frontend
npm install
npm run dev
```

Expected:
- Frontend dev server starts on `http://localhost:5173`
- Vite proxy forwards API calls like `/auth/login` and `/scan` to `http://127.0.0.1:5000` (see `frontend/vite.config.js`).

### 1.3 Optional: Redis + Celery (async scanning)

The backend can run scans synchronously **without** Redis/Celery.

If Redis is available and you set `USE_CELERY=true` (and the broker URLs), `/scan` will queue a Celery task and return `202` with `{status:"queued", task_id}`; the UI will poll `/scan/status/<task_id>`.

---

## 2) End-to-end runtime flow (what happens when you click things)

### 2.1 Authentication flow (frontend → backend)

1. User signs up in UI (`frontend/src/Signup.jsx`) → POST `/auth/signup`.
2. User logs in (`frontend/src/Login.jsx`) → POST `/auth/login`.
3. Backend returns `{access_token, refresh_token, expires_in}`.
4. Frontend stores:
   - access token in `sessionStorage` (key: `ssa_access_token`)
   - refresh token in `localStorage` (key: `ssa_refresh_token`)
   - expiry timestamp in `localStorage` (key: `ssa_token_expiry`)
   via `frontend/src/api.js` (`TokenManager`).
5. Requests to protected endpoints include `Authorization: Bearer <access_token>`.
6. If access token expires, the API client auto-calls `/auth/refresh` using refresh token.

Access-token lifetime:
- Backend issues access tokens for ~15 minutes (`expires_in` returned in login response).

Refresh-token lifetime:
- Refresh tokens are persisted in DB and typically last days (implementation in `backend/app.py`).

Security details:
- Backend enforces password strength and account lockout.
- Backend uses refresh token DB records for logout/revocation.

### 2.2 Scan flow (frontend → backend → worker/sync)

**UI entry:** `frontend/src/SiteSecurityAnalyzer.jsx`.

1. UI collects a URL.
2. UI calls POST `/scan` with JSON `{url: "..."}` and a Bearer token.
3. Backend validates URL for SSRF safety (see `validate_url_safe()` in `backend/app.py`).
4. Backend checks Redis cache if Redis is available.
5. Two execution modes:

**A) Sync mode (default if Redis/Celery not active)**
- Backend runs the scan in-process by calling helper functions from `backend/celery_tasks.py`.
- Builds the standardized report via `backend/core/report_builder.py`.
- Saves scan record in DB.
- Returns a full response with `score`, `report`, `findings`, `explanation`, etc.

**B) Async mode (if `USE_CELERY=true` and Redis broker works)**
- Backend queues Celery task `perform_security_scan.delay(url, user_id)`.
- Returns `202` with `{status:"queued", task_id}`.
- UI polls GET `/scan/status/<task_id>` every ~2 seconds.
- Once complete, UI renders result.

Typical scan response shape (sync/cached):

```json
{
  "score": 85,
  "report": {"https": true, "hsts": true, "content_security_policy": false, "dns_spf": true, "dns_dmarc": false},
  "findings": {
    "url": "https://example.com",
    "headers": {"strict_transport_security": {"present": true, "severity": "pass"}},
    "cookies": {"has_secure": true, "has_httponly": true, "missing_samesite": 1},
    "dns": {"spf": {"present": true}, "dmarc": {"present": false}}
  },
  "priority_actions": [
    {"title": "Add a Content-Security-Policy", "severity": "high", "why": "...", "how": "..."}
  ],
  "risk_snapshot": {"overall": "moderate", "top_risks": ["Missing CSP"]},
  "explanation": "<p>...sanitized by frontend before render...</p>"
}
```

Queued scan response shape:

```json
{"status": "queued", "task_id": "<celery-task-id>"}
```

### 2.3 History flow (frontend → backend)

- UI route `/history` (`frontend/src/History.jsx`) fetches GET `/auth/history`.
- Backend returns user’s scans ordered by time with stored report payloads.

---

## 3) Backend deep dive (`backend/`)

### 3.1 Backend entrypoint: `backend/app.py`

**What it is:**
- The main Flask API server.
- Holds auth endpoints, scan endpoints, SSRF defenses, rate limiting, Prometheus metrics, and DB initialization.

#### 3.1.1 Startup configuration and strict env checks

At import/startup:
- Loads `.env` via `python-dotenv` (`load_dotenv()`).
- Requires:
  - `SECRET_KEY` length ≥ 64 (crashes otherwise)
  - `DATABASE_URL` present (crashes otherwise)

This is why “backend won’t start” unless those env vars are set.

#### 3.1.2 Database (SQLAlchemy + Flask-Migrate)

Models in `backend/app.py`:

- `User`
  - `id`, `email`, `password_hash`
  - security controls: `failed_login_attempts`, `account_locked_until`
  - password reset: `reset_token_hash`, `reset_token_expires_at`, `reset_token_used_at`
  - timestamps

- `RefreshToken`
  - persisted refresh tokens (supports rotation/revocation)
  - `token_hash`, `expires_at`, `revoked_at`

- `Scan`
  - `url`, `domain`
  - `report` JSON (the flat contract)
  - `full_result` JSON (enriched data)
  - `created_at`

`init_db()` runs `db.create_all()` and checks that `users`, `refresh_tokens`, and `scans` exist.

Important: `init_db()` is called both:
- in `if __name__ == "__main__":` before `app.run(...)`, and
- at import time (bottom of file), so WSGI servers also trigger schema creation.

#### 3.1.3 Security headers + CORS + production hardening

- CORS: `flask-cors` is configured with allowed origins from `ALLOWED_ORIGINS` (or localhost defaults).
- Production-only hardening: `Flask-Talisman` sets CSP and other headers when `FLASK_ENV=production`.
- `after_request` sets basic headers like `X-Content-Type-Options`, etc.

#### 3.1.4 Rate limiting

- Uses `Flask-Limiter`.
- In non-production, limiter is effectively disabled via very high limits.
- In production, default limits apply and specific endpoints also use per-route limits.

Concrete per-route limits (as implemented in `backend/app.py`):
- `/auth/signup`: very low (anti-abuse)
- `/auth/login`: higher but still throttled
- `/scan`: limited per hour (scans are “expensive”)
- `/auth/forgot-password` and `/auth/reset-password`: throttled

#### 3.1.5 Auth endpoints (summary)

- `POST /auth/signup`
  - validates email + password strength
  - stores user with hashed password

- `POST /auth/login`
  - checks lockout
  - verifies password
  - issues access token (short-lived) + refresh token (DB-backed)

- `POST /auth/refresh`
  - validates refresh token against DB record
  - issues new access token

- `POST /auth/logout`
  - revokes refresh token

- `POST /auth/forgot-password`
  - generates a reset token
  - returns generic message to avoid email enumeration
  - in development, reset token is often logged (check logs)

- `POST /auth/reset-password`
  - validates reset token hash + expiry + “used” status
  - updates password, marks token as used

- `GET /auth/history` (auth required)
  - returns list of scans for the current user

Auth middleware:
- `auth_required` decorator validates `Authorization` header bearer JWT.

Login response payload:
- includes both tokens and a small `user` object.

Logout behavior:
- backend attempts to revoke the refresh token in DB so refresh no longer works.

#### 3.1.6 SSRF defenses (critical: scan endpoint safety)

`validate_url_safe(url)` performs:
- Normalization (ensures scheme is http/https)
- DNS resolution (A and AAAA)
- IP address classification blocks:
  - private, loopback, link-local, multicast
  - reserved ranges
  - cloud metadata endpoints (explicit checks)
- Special-case allow: IPv6 NAT64 prefix `64:ff9b::/96`.

This is paired with redirect validation in the HTTP client (see `SafeHTTPAdapter` in `backend/celery_tasks.py`).

Other scan-safety limits worth knowing (implemented in the scan utilities):
- strict http/https scheme allow-list
- conservative timeouts (connect + read)
- response size cap when reading response bodies

#### 3.1.7 Scan endpoints

- `POST /scan` (auth required)
  - optional Redis cache hit
  - async if Celery is enabled and broker is reachable
  - else sync scan

- `GET /scan/status/<task_id>` (auth required)
  - checks Celery task status and returns `processing|complete|failed`

#### 3.1.8 Health/ready/metrics

- `/health` and `/ready` endpoints expose status checks.
- Prometheus exporter provides `/metrics`.

When troubleshooting “frontend can’t talk to backend”, always verify `/health` first.

---

### 3.2 Async worker + scan utilities: `backend/celery_tasks.py`

This file serves two roles:

1) **Reusable scanning utilities** (used by sync path in `backend/app.py`).
2) **Celery task(s)** (used when queue mode is enabled).

Key components:

- `SafeHTTPAdapter`
  - intercepts redirects
  - re-validates redirect target host/IP against SSRF rules (mitigates DNS rebinding / redirect-to-private)

- `create_safe_session()`
  - builds a `requests.Session` with:
    - retry policy
    - timeouts
    - user-agent
    - redirect limits
    - CA trust configuration (certifi/truststore)

- Core scan steps (high-level):
  - fetch headers
  - analyze security headers
  - analyze cookies (secure/httponly/samesite)
  - DNS lookups for SPF/DMARC
  - compute score and severity mapping
  - build explanation HTML
  - enrich with `core/report_builder.py`

- Celery task: `perform_security_scan(url, user_id)`
  - runs scan
  - saves scan to DB
  - caches in Redis (if configured)

---

### 3.3 Report shaping contract: `backend/core/report_builder.py`

The frontend is built around a **stable “flat report”** contract: a JSON object with predictable boolean-ish keys.

`report_builder.py` converts raw findings into:

- `build_flat_report(findings)` → booleans like:
  - `https`, `hsts`, `content_security_policy`, `x_frame_options`, `x_content_type_options`, `referrer_policy`, `permissions_policy`, `dns_spf`, `dns_dmarc`, `server_header`, etc.

- `build_priority_actions(...)` → list of remediation actions.
- `build_risk_snapshot(...)` → high-level risk summary.
- `build_explanation(...)` → human-readable HTML content.
- `enrich_scan_result(...)` → attaches report + explanation + score + actions.

This is the “backend → frontend contract” that keeps UI logic simple.

---

### 3.4 “Advanced scanner” modules (prototype / not fully wired)

Folder: `backend/core/`

- `crawler.py`
- `intelligence_engine.py`
- `attack_graph.py`
- `exploit_generator.py`

These look like aspirational modules for deeper crawling, vuln inference, and attack-graph style reporting. In the current runtime, the production `/scan` route mainly uses the simpler header/DNS-based scanner path and the report builder.

---

### 3.5 Backend scripts and tests

- `backend/create_test_user.py` / `backend/debug_login.py` — helper scripts for local debugging.
- `backend/check_user.py` — inspects a specific user record and tests password checks.
- `backend/test_auth.py` — quick end-to-end signup/login/refresh test against a running backend.
- `backend/load_test.py` — load testing (Locust).
- `backend/scripts/ci_scan.py` — CI scanning script; currently references modules that may not exist (see “Known inconsistencies”).
- `backend/tests/` — pytest tests for scanning.

Top-level tests:
- `test_auth_flow.py`, `test_auth_fresh.py`, `test_user_db.py`, etc. — higher-level tests that exercise auth/scanning.

---

## 4) Frontend deep dive (`frontend/`)

### 4.1 Tooling

- Vite + React (`frontend/vite.config.js`)
- Tailwind (`frontend/tailwind.config.js`, `frontend/src/index.css`)

Key styling primitives:
- `frontend/src/index.css` defines `.btn-brutal`, `.input-brutal`, `.card-brutal`, and shadow utilities.
- `frontend/src/SiteSecurityAnalyzer.css` contains a small set of custom overrides (animations + scrollbar).

The dev setup assumes:
- frontend runs at `http://localhost:5173`
- backend runs at `http://127.0.0.1:5000`

### 4.2 Routing

Entry: `frontend/src/main.jsx`

Routes:
- `/` → `Landing.jsx`
- `/login` → `Login.jsx`
- `/signup` → `Signup.jsx`
- `/forgot-password` → `ForgotPassword.jsx`
- `/reset-password` → `ResetPassword.jsx`
- `/learn` → `Learn.jsx`
- `/debug-login` → `LoginDebug.jsx` (debug helper)

Protected routes (`frontend/src/ProtectedRoute.jsx`):
- `/analyze` → `SiteSecurityAnalyzer.jsx`
- `/history` → `History.jsx`

Layout wrapper:
- `Layout.jsx` renders `Header` + `Outlet` + `Footer`.

Header behavior (`frontend/src/Header.jsx`):
- checks `api.isAuthenticated()` to decide whether to show login buttons vs logout
- `logout` calls `api.logout()` then forces a reload

### 4.3 API client + token model: `frontend/src/api.js`

This is the browser-side “SDK” for the backend.

- `TokenManager`
  - access token: `sessionStorage['ssa_access_token']`
  - refresh token: `localStorage['ssa_refresh_token']`
  - expiry: `localStorage['ssa_token_expiry']`

- Auto-refresh behavior:
  - When requests get a 401, the client tries `/auth/refresh` and retries.

Important implementation detail:
- Several components include comments warning not to use old/stale token keys like `localStorage['auth_token']`.

### 4.4 Analyzer UI: `frontend/src/SiteSecurityAnalyzer.jsx`

What it does:
- validates/sanitizes input URL
- posts `/scan`
- handles 3 response shapes:
  1) sync scan result (immediate)
  2) cached scan result (immediate)
  3) queued scan result: `{status:"queued", task_id}` → poll `/scan/status/<task_id>`

XSS defense:
- uses DOMPurify to sanitize HTML-like content rendered from backend (explanation, etc.).

### 4.5 History UI: `frontend/src/History.jsx`

- fetches `/auth/history`
- computes a score client-side from the stored `report`
- supports search, filtering, sorting, pagination, and CSV export

### 4.6 Learn UI: `frontend/src/Learn.jsx`

- purely static educational content
- uses Radix accordion component in `frontend/src/components/ui/accordion.jsx`

Accordion helper:
- `frontend/src/components/ui/accordion.jsx` wraps Radix primitives and uses `frontend/src/lib/utils.js` for class merging (`cn()`).

### 4.7 Dark mode

- `frontend/src/DarkModeContext.jsx` stores preference in `localStorage['darkMode']` and toggles `document.documentElement.classList`.

---

## 5) Browser extension deep dive (`extension/`)

### 5.1 `extension/manifest.json`

- MV3 manifest
- permissions: `activeTab`, `storage`, `alarms`
- service worker: `background.js`
- content script: `content.js` on `<all_urls>`
- popup UI: `popup.html` + `popup.css` + `popup.js`

### 5.2 Popup runtime behavior: `extension/popup.js`

- Implements its own mini auth client:
  - logs into backend at `http://127.0.0.1:5000/auth/login`
  - stores tokens in `chrome.storage.local` (`ssa_access_token`, `ssa_refresh_token`, `ssa_token_expiry`)
  - refreshes access token via `/auth/refresh`

- Scan button:
  - gets active tab URL
  - POST `/scan` with bearer token
  - if queued: poll `/scan/status/<task_id>`
  - renders score and selected header findings
  - links out to the full web app at `http://localhost:5173/analyze?url=<domain>`

  Extension token model:
  - Stored in `chrome.storage.local` (not `localStorage`):
    - `ssa_access_token`
    - `ssa_refresh_token`
    - `ssa_token_expiry`

### 5.3 Background worker: `extension/background.js`

- sets an alarm every 60 minutes
- clears expired access tokens (keeps refresh token)

### 5.4 Content script: `extension/content.js`

- responds to message `scanDOM`
- extracts client-side hints:
  - insecure forms
  - mixed content
  - meta tag count
  - inline vs external script counts

This data is currently not wired into backend scan results; it’s available for future enrichment.

---

## 6) Infra / deployment configs (what they intend vs what actually matches)

### 6.1 Docker Compose: `docker-compose.yml`

Intended services:
- Postgres
- Redis
- backend
- celery worker
- celery beat
- prometheus
- grafana
- nginx

**Current mismatch to be aware of:**
- Compose maps backend `5000:5000`, but `backend/Dockerfile` runs gunicorn bound to `:8080`.

Other compose expectations:
- `nginx/nginx.conf` expects backend service name `backend` and port 5000.
- Prometheus scrape config expects `/metrics` on backend.

### 6.2 Backend container: `backend/Dockerfile`

- sets `PORT=8080`
- runs `gunicorn -b :8080 ... app:app`

This can work on platforms like Cloud Run/Render if routing expects 8080.

### 6.3 Root Dockerfile: `Dockerfile`

- copies backend into `/app`
- exposes 8080
- runs `./start.sh`

**But `backend/start.sh` currently runs `gunicorn app_secure:app`**, which does not match the repo’s actual `backend/app.py` module name.

Practical note:
- If you want a working container right now, the easiest route is to run `gunicorn app:app` from inside the `backend/` image (or fix the start script).

### 6.4 Nginx: `nginx/nginx.conf`

- designed for HTTPS termination + rate limiting
- proxies upstream backend at `backend:5000`

### 6.5 Prometheus: `monitoring/prometheus.yml`

- scrapes backend `/metrics`
- references exporters (`postgres-exporter`, `redis-exporter`, `node-exporter`) that are not defined in `docker-compose.yml`.

### 6.6 Cloud Build: `cloudbuild.yaml`

- deploys backend to Cloud Run from `backend/`
- builds frontend and deploys to Firebase Hosting

---

## 7) One-off scripts at repo root (not runtime)

These scripts are convenience tools used by the repo author; they are not imported by the running app.

- `cleanup_ui.py`, `refactor_ui.py`, `polish_ui.py`
  - mass-edit `frontend/src/**/*.jsx` class strings
  - contain absolute paths to the original author’s machine

- `patch_backend.py`
  - patches time handling and NAT64 SSRF checks in backend files
  - contains absolute paths; assumes older code strings

- `find_syntax.py`
  - quick scan for suspicious ternary usage in JSX

- `fix_user.py`
  - resets/creates a specific test user in a local SQLite db
  - useful when you’ve locked yourself out via auth lockout logic

- `migrate.py`
  - attempts to replace files with “*_secure” versions
  - currently references files that may not exist in this repo state

---

## 8) Known inconsistencies / stale docs (important)

Several docs reference files that are not present in the current working tree.

Examples:

- `README.md` mentions FastAPI `app_advanced.py` and `core/risk_scorer.py` — not present in the current tree.
- `SECURITY_FIXES.md` and `COMPLETE.md` reference `backend/app_secure.py`, `frontend/src/api_secure.js`, `extension/popup_secure.js`, etc. — those secure variants are not present.
- `backend/start.sh` and `backend/start_production.sh` run `gunicorn app_secure:app` — but the current backend entrypoint is `backend/app.py` with Flask `app`.
- `docker-compose.yml` expects backend on port 5000, but `backend/Dockerfile` binds to 8080.

**Practical impact:**
- For local development, ignore `start.sh`/compose and run `python backend/app.py` + `npm run dev`.

CI script mismatch:
- `backend/scripts/ci_scan.py` imports `core.risk_scorer` which is not present, so it will fail until that module exists (or the import is updated).

---

## 9) “If you want to clean this repo up” (optional next steps)

If you want, the repo can be made consistent by:

1) Aligning Docker + compose ports (choose 5000 or 8080 end-to-end).
2) Fixing `backend/start.sh` to run `gunicorn app:app` (or renaming modules consistently).
3) Updating docs to match the actual code in `backend/app.py`.
4) Either removing or re-adding the “*_secure” files referenced by docs.

---

## 10) Quick smoke test checklist (manual)

Once backend + frontend are running:

- Backend:
  - `GET http://127.0.0.1:5000/health`
  - `GET http://127.0.0.1:5000/metrics`

- Frontend:
  - open `http://localhost:5173`
  - sign up → login → analyze `https://example.com`
  - check history shows scans

- Extension:
  - load unpacked extension from `extension/`
  - log in in popup
  - scan active tab

