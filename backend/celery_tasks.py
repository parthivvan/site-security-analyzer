"""
Celery Tasks for Asynchronous Security Scanning
Handles all long-running scan operations outside the request cycle.
"""
import os
import json
import time
import socket
import ipaddress
import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import dns.resolver
from celery import Celery, Task
from celery.schedules import crontab
import redis

# Inject Windows system certificates so HTTPS works without cert errors
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# Initialize Celery
celery = Celery('scanner_tasks')

# Configuration
celery.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=120,  # Kill task after 120s (2 minutes for complex sites)
    task_soft_time_limit=110,  # Warn at 110s
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
)

# Redis for caching
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ──────────────────────────────────────────────────────────────────────
# Standalone SQLAlchemy session for the Celery worker process.
# We intentionally do NOT import from app.py to avoid re-running all
# Flask app-factory side-effects (JWT validation, CORS setup, etc.)
# ──────────────────────────────────────────────────────────────────────
from sqlalchemy import create_engine, text as _text
from sqlalchemy.orm import sessionmaker, scoped_session
import datetime as _dt

_DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///scanner.db')
# Map legacy postgres:// scheme → postgresql://
if _DATABASE_URL.startswith('postgres://'):
    _DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# For relative SQLite paths, resolve to Flask's instance/ folder so both
# Flask and Celery workers share the exact same file.
if _DATABASE_URL.startswith('sqlite:///') and not _DATABASE_URL.startswith('sqlite:////'):
    _db_filename = _DATABASE_URL[len('sqlite:///'):]
    if not os.path.isabs(_db_filename):
        # Resolve relative to the backend directory's instance/ subfolder
        _backend_dir = os.path.dirname(os.path.abspath(__file__))
        _db_filename = os.path.join(_backend_dir, 'instance', _db_filename)
        _DATABASE_URL = 'sqlite:///' + _db_filename

_engine_kwargs: dict = {}
if _DATABASE_URL.startswith(('postgresql', 'postgres')):
    _engine_kwargs = {'pool_pre_ping': True, 'pool_size': 5, 'max_overflow': 10}
else:
    _engine_kwargs = {'connect_args': {'check_same_thread': False}}

_engine = create_engine(_DATABASE_URL, **_engine_kwargs)
_SessionFactory = scoped_session(sessionmaker(bind=_engine))

def _save_scan(user_id: int, url: str, domain: str, score: int,
               flat_report: dict, duration_ms: int):
    """Save a scan result directly via raw SQL (avoids Flask app import cycles)."""
    session = _SessionFactory()
    try:
        session.execute(
            _text(
                # 'scans' is the Flask model's table name (plural)
                "INSERT INTO scans (user_id, url, domain, score, report, scan_duration_ms, created_at)"
                " VALUES (:uid, :url, :domain, :score, :report, :dur, :ts)"
            ),
            {
                'uid': user_id, 'url': url, 'domain': domain,
                'score': score, 'report': json.dumps(flat_report),
                'dur': duration_ms, 'ts': _dt.datetime.utcnow().isoformat(),
            }
        )
        session.commit()
    except Exception as exc:
        session.rollback()
        raise exc
    finally:
        _SessionFactory.remove()

# Scan configuration
SCAN_TIMEOUT = int(os.environ.get('SCAN_TIMEOUT_SECONDS', 30))  # Increased to 30s for complex sites
MAX_RESPONSE_SIZE = int(os.environ.get('MAX_RESPONSE_SIZE_MB', 10)) * 1024 * 1024
MAX_REDIRECTS = int(os.environ.get('MAX_REDIRECTS', 3))


class SafeHTTPAdapter(HTTPAdapter):
    """Custom HTTP adapter with additional SSRF protection on redirects."""
    
    def send(self, request, **kwargs):
        # Revalidate DNS on EVERY request (including redirects)
        hostname = urlparse(request.url).hostname
        
        if hostname:
            try:
                resolved_ips = socket.getaddrinfo(hostname, None)
                for ip_tuple in resolved_ips:
                    ip_str = ip_tuple[4][0]
                    if '%' in ip_str:
                        ip_str = ip_str.split('%')[0]
                    
                    ip_obj = ipaddress.ip_address(ip_str)
                    
                    if (ip_obj.is_private or ip_obj.is_loopback or 
                        ip_obj.is_link_local or ip_obj.is_multicast or 
                        ip_obj.is_reserved):
                        raise requests.exceptions.ConnectionError(
                            f"Blocked private IP in redirect: {ip_str}"
                        )
            except socket.gaierror:
                raise requests.exceptions.ConnectionError("DNS resolution failed")
        
        return super().send(request, **kwargs)


def create_safe_session() -> requests.Session:
    """Create HTTP session with safety measures."""
    session = requests.Session()

    # Use certifi CA bundle so HTTPS works on all platforms (especially Windows)
    try:
        import certifi
        session.verify = certifi.where()
    except ImportError:
        pass  # fall back to default (may fail on Windows without system certs)
    
    # Add retry logic
    retry_strategy = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    
    # Mount adapters
    session.mount('http://', SafeHTTPAdapter(max_retries=retry_strategy))
    session.mount('https://', SafeHTTPAdapter(max_retries=retry_strategy))
    
    # Set custom User-Agent
    session.headers.update({
        'User-Agent': 'SecurityScanner/2.0 (+https://yourapp.com/about; security@yourapp.com)',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'DNT': '1',
    })

    # Limit redirects to prevent open-redirect abuse (must be set on session, not per-request)
    session.max_redirects = MAX_REDIRECTS

    return session


def analyze_security_headers(headers: Dict[str, str], url: str) -> Dict[str, Any]:
    """
    Enhanced security header analysis.
    
    Returns detailed findings for each security header including:
    - Presence check
    - Value validation
    - Security score
    - Recommendations
    """
    findings = {}
    
    # HTTPS Check
    findings['https'] = {
        'present': url.startswith('https://'),
        'score': 15 if url.startswith('https://') else 0,
        'severity': 'critical' if not url.startswith('https://') else 'pass',
        'details': 'HTTPS encrypts traffic' if url.startswith('https://') else 'No HTTPS - traffic can be intercepted'
    }
    
    # HSTS (Strict-Transport-Security)
    hsts = headers.get('Strict-Transport-Security', '')
    if hsts:
        import re
        max_age_match = re.search(r'max-age=(\d+)', hsts)
        max_age = int(max_age_match.group(1)) if max_age_match else 0
        
        has_subdomains = 'includeSubDomains' in hsts
        has_preload = 'preload' in hsts
        
        if max_age >= 31536000 and has_subdomains:
            score = 15
            severity = 'pass'
        elif max_age >= 31536000:
            score = 10
            severity = 'info'
        elif max_age > 0:
            score = 5
            severity = 'warning'
        else:
            score = 0
            severity = 'fail'
        
        findings['hsts'] = {
            'present': True,
            'value': hsts,
            'max_age': max_age,
            'includeSubDomains': has_subdomains,
            'preload': has_preload,
            'score': score,
            'severity': severity,
            'details': f"HSTS enforces HTTPS for {max_age} seconds"
        }
    else:
        findings['hsts'] = {
            'present': False,
            'score': 0,
            'severity': 'critical',
            'details': 'Missing HSTS - vulnerable to protocol downgrade attacks'
        }
    
    # CSP (Content-Security-Policy)
    csp = headers.get('Content-Security-Policy', '')
    if csp:
        issues = []
        if "'unsafe-inline'" in csp:
            issues.append("unsafe-inline allows inline scripts")
        if "'unsafe-eval'" in csp:
            issues.append("unsafe-eval allows eval()")
        if ' * ' in csp or csp.endswith(' *'):
            issues.append("wildcard (*) allows any source")
        
        if not issues:
            score = 20
            severity = 'pass'
        else:
            score = 10
            severity = 'warning'
        
        findings['csp'] = {
            'present': True,
            'value': csp[:200] + '...' if len(csp) > 200 else csp,
            'issues': issues,
            'score': score,
            'severity': severity,
            'details': 'CSP protects against XSS and injection attacks'
        }
    else:
        findings['csp'] = {
            'present': False,
            'score': 0,
            'severity': 'high',
            'details': 'Missing CSP - vulnerable to XSS attacks'
        }
    
    # X-Frame-Options
    xfo = headers.get('X-Frame-Options', '').upper()
    if xfo in ('DENY', 'SAMEORIGIN'):
        findings['x_frame_options'] = {
            'present': True,
            'value': xfo,
            'score': 10,
            'severity': 'pass',
            'details': f'{xfo} prevents clickjacking'
        }
    elif xfo:
        findings['x_frame_options'] = {
            'present': True,
            'value': xfo,
            'score': 5,
            'severity': 'warning',
            'details': 'Weak X-Frame-Options value'
        }
    else:
        findings['x_frame_options'] = {
            'present': False,
            'score': 0,
            'severity': 'medium',
            'details': 'Missing X-Frame-Options - vulnerable to clickjacking'
        }
    
    # X-Content-Type-Options
    xcto = headers.get('X-Content-Type-Options', '').lower()
    findings['x_content_type_options'] = {
        'present': xcto == 'nosniff',
        'value': xcto if xcto else None,
        'score': 5 if xcto == 'nosniff' else 0,
        'severity': 'pass' if xcto == 'nosniff' else 'medium',
        'details': 'Prevents MIME-type sniffing' if xcto == 'nosniff' else 'Missing - vulnerable to MIME sniffing'
    }
    
    # Referrer-Policy
    rp = headers.get('Referrer-Policy', '')
    secure_policies = ['no-referrer', 'same-origin', 'strict-origin', 'strict-origin-when-cross-origin']
    findings['referrer_policy'] = {
        'present': bool(rp),
        'value': rp if rp else None,
        'score': 5 if any(p in rp for p in secure_policies) else 0,
        'severity': 'pass' if rp else 'low',
        'details': 'Controls referrer information leakage' if rp else 'Missing - referrer data may leak'
    }
    
    # Permissions-Policy / Feature-Policy
    pp = headers.get('Permissions-Policy', headers.get('Feature-Policy', ''))
    findings['permissions_policy'] = {
        'present': bool(pp),
        'value': pp[:200] + '...' if len(pp) > 200 else pp,
        'score': 5 if pp else 0,
        'severity': 'pass' if pp else 'low',
        'details': 'Controls browser features' if pp else 'Missing - no control over browser features'
    }
    
    # X-XSS-Protection (deprecated but check for incorrect usage)
    xxp = headers.get('X-XSS-Protection', '')
    if xxp == '0':
        findings['x_xss_protection'] = {
            'present': True,
            'value': '0',
            'score': 0,
            'severity': 'info',
            'details': 'Correctly disabled (deprecated header, CSP is better)'
        }
    elif xxp:
        findings['x_xss_protection'] = {
            'present': True,
            'value': xxp,
            'score': -5,
            'severity': 'warning',
            'details': 'Should be set to 0 or removed (deprecated, can introduce vulnerabilities)'
        }
    
    # Server Header (info disclosure)
    server = headers.get('Server', '')
    if server:
        findings['server_disclosure'] = {
            'present': True,
            'value': server,
            'score': -3,
            'severity': 'info',
            'details': f'Server version disclosed: {server}'
        }
    
    # X-Powered-By (info disclosure)
    xpb = headers.get('X-Powered-By', '')
    if xpb:
        findings['x_powered_by'] = {
            'present': True,
            'value': xpb,
            'score': -3,
            'severity': 'info',
            'details': f'Technology stack disclosed: {xpb}'
        }
    
    return findings


def analyze_cookies(headers: Dict[str, str]) -> Dict[str, Any]:
    """Analyze cookie security."""
    set_cookie = headers.get('Set-Cookie', '')
    
    if not set_cookie:
        return {'present': False, 'score': 0}
    
    issues = []
    
    if 'Secure' not in set_cookie:
        issues.append('Missing Secure flag')
    if 'HttpOnly' not in set_cookie:
        issues.append('Missing HttpOnly flag')
    if 'SameSite' not in set_cookie:
        issues.append('Missing SameSite attribute')
    
    return {
        'present': True,
        'issues': issues,
        'score': 0 if issues else 5,
        'severity': 'warning' if issues else 'pass',
        'details': f"Cookie security issues: {', '.join(issues)}" if issues else 'Cookies properly secured'
    }


def check_dns_records(domain: str) -> Dict[str, Any]:
    """Check DNS security records (SPF, DMARC, DNSSEC)."""
    findings = {}
    
    # SPF Check
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT', lifetime=5)
        spf_found = False
        spf_record = None
        
        for rdata in txt_records:
            txt_str = rdata.to_text().strip('"')
            if txt_str.startswith('v=spf1'):
                spf_found = True
                spf_record = txt_str
                break
        
        findings['spf'] = {
            'present': spf_found,
            'record': spf_record,
            'score': 5 if spf_found else 0,
            'severity': 'pass' if spf_found else 'medium',
            'details': 'SPF protects against email spoofing' if spf_found else 'No SPF record found'
        }
    except Exception as e:
        findings['spf'] = {
            'present': False,
            'score': 0,
            'severity': 'medium',
            'details': f'SPF lookup failed: {str(e)}'
        }
    
    # DMARC Check
    try:
        dmarc_domain = f'_dmarc.{domain}'
        dmarc_records = dns.resolver.resolve(dmarc_domain, 'TXT', lifetime=5)
        dmarc_found = False
        dmarc_record = None
        
        for rdata in dmarc_records:
            txt_str = rdata.to_text().strip('"')
            if txt_str.startswith('v=DMARC1'):
                dmarc_found = True
                dmarc_record = txt_str
                break
        
        findings['dmarc'] = {
            'present': dmarc_found,
            'record': dmarc_record,
            'score': 5 if dmarc_found else 0,
            'severity': 'pass' if dmarc_found else 'medium',
            'details': 'DMARC provides email authentication' if dmarc_found else 'No DMARC record found'
        }
    except Exception as e:
        findings['dmarc'] = {
            'present': False,
            'score': 0,
            'severity': 'medium',
            'details': f'DMARC lookup failed: {str(e)}'
        }
    
    return findings


def calculate_overall_score(findings: Dict[str, Any]) -> int:
    """Calculate overall security score from detailed findings."""
    total_score = 50  # Base score
    
    for category, data in findings.items():
        if isinstance(data, dict) and 'score' in data:
            total_score += data['score']
    
    return max(0, min(100, total_score))


@celery.task(bind=True, name='scanner.perform_security_scan')
def perform_security_scan(self, url: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform comprehensive security scan.
    
    This task runs asynchronously in Celery worker.
    Includes all security checks with proper error handling.
    """
    start_time = time.time()
    
    try:
        self.update_state(state='PROGRESS', meta={'progress': 10, 'stage': 'Resolving DNS'})
        
        parsed = urlparse(url)
        domain = parsed.hostname
        
        # Create safe session
        session = create_safe_session()
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 20, 'stage': 'Fetching headers'})
        
        # Make request with all safety measures
        response = session.get(
            url,
            timeout=(5, SCAN_TIMEOUT),  # (connect, read) timeout
            allow_redirects=True,
            stream=True
        )
        
        # Check content length before downloading
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            return {
                'error': 'Response too large',
                'url': url,
                'domain': domain
            }
        
        # Read with limit
        content = response.raw.read(MAX_RESPONSE_SIZE, decode_content=True)
        if len(content) >= MAX_RESPONSE_SIZE:
            return {
                'error': 'Response too large',
                'url': url,
                'domain': domain
            }
        
        headers = dict(response.headers)
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 50, 'stage': 'Analyzing headers'})
        
        # Analyze security headers
        header_findings = analyze_security_headers(headers, response.url)
        
        # Analyze cookies
        cookie_findings = analyze_cookies(headers)
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 70, 'stage': 'Checking DNS'})
        
        # Check DNS records
        dns_findings = check_dns_records(domain)
        
        # Combine all findings
        all_findings = {
            'headers': header_findings,
            'cookies': cookie_findings,
            'dns': dns_findings
        }
        
        # Calculate score
        score = calculate_overall_score({**header_findings, **cookie_findings, **dns_findings})

        # Build flat report — flat boolean keys that the frontend computeScore() expects.
        # NOTE: celery_tasks uses 'csp' internally but the DB/frontend expect 'content_security_policy'.
        flat_report = {
            'https':                   header_findings.get('https', {}).get('present', False),
            'hsts':                    header_findings.get('hsts', {}).get('present', False),
            'content_security_policy': header_findings.get('csp', {}).get('present', False),
            'x_frame_options':         header_findings.get('x_frame_options', {}).get('present', False),
            'x_content_type_options':  header_findings.get('x_content_type_options', {}).get('present', False),
            'referrer_policy':         header_findings.get('referrer_policy', {}).get('present', False),
            'permissions_policy':      header_findings.get('permissions_policy', {}).get('present', False),
            # server_disclosure key means the header IS present (leaking info), so True is bad
            'server_header':           header_findings.get('server_disclosure', {}).get('present', False),
            'dns_spf':                 dns_findings.get('spf', {}).get('present', False),
            'dns_dmarc':               dns_findings.get('dmarc', {}).get('present', False),
        }

        # Build human-readable explanation for the frontend panel
        passed = [k for k, v in flat_report.items() if k != 'server_header' and v]
        failed = [k for k, v in flat_report.items() if k != 'server_header' and not v]
        label_map = {
            'https': 'HTTPS', 'hsts': 'HSTS', 'content_security_policy': 'CSP',
            'x_frame_options': 'X-Frame-Options', 'x_content_type_options': 'X-Content-Type-Options',
            'referrer_policy': 'Referrer-Policy', 'permissions_policy': 'Permissions-Policy',
            'dns_spf': 'SPF', 'dns_dmarc': 'DMARC',
        }
        passed_labels = ', '.join(label_map.get(k, k) for k in passed) or 'None'
        failed_labels = ', '.join(label_map.get(k, k) for k in failed) or 'None'
        if score >= 80:
            grade = 'Excellent'
        elif score >= 60:
            grade = 'Good'
        elif score >= 40:
            grade = 'Moderate'
        else:
            grade = 'Critical'
        explanation = (
            f'<strong>Security Grade: {grade} ({score}/100)</strong><br>'
            f'<strong>Passed ({len(passed)}):</strong> {passed_labels}<br>'
            f'<strong>Failed ({len(failed)}):</strong> {failed_labels}'
            + (' <br><em>⚠️ Server version is disclosed in response headers.</em>' if flat_report.get('server_header') else '')
        )

        # Update progress
        self.update_state(state='PROGRESS', meta={'progress': 90, 'stage': 'Saving results'})

        # Prepare result — 'report' uses the flat format so frontend score functions work correctly
        result = {
            'url': url,
            'domain': domain,
            'score': score,
            'report': flat_report,        # flat booleans for frontend computeScore()
            'findings': all_findings,     # rich nested data for detailed view
            'explanation': explanation,
            'final_url': response.url,
            'status_code': response.status_code,
            'scan_duration_ms': int((time.time() - start_time) * 1000),
            'scanned_at': datetime.datetime.utcnow().isoformat()
        }
        
        # Cache result (1 hour)
        cache_key = f"scan:{domain}"
        redis_client.setex(cache_key, 3600, json.dumps(result))
        
        # Save to database
        if user_id:
            try:
                _save_scan(user_id, url, domain, score, flat_report,
                           result['scan_duration_ms'])
            except Exception as db_err:
                # Don't fail the whole scan for a DB write error
                result['db_error'] = str(db_err)
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            'error': 'Request timeout - site took too long to respond',
            'url': url,
            'domain': domain
        }
    except requests.exceptions.SSLError as e:
        return {
            'error': f'SSL/TLS error: {str(e)}',
            'url': url,
            'domain': domain
        }
    except requests.exceptions.ConnectionError as e:
        return {
            'error': f'Connection error: {str(e)}',
            'url': url,
            'domain': domain
        }
    except Exception as e:
        return {
            'error': f'Scan failed: {str(e)}',
            'url': url,
            'domain': domain
        }


@celery.task(name='scanner.cleanup_old_scans')
def cleanup_old_scans():
    """Scheduled task to clean up scans older than 90 days."""
    from app import db, Scan
    
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    deleted = Scan.query.filter(Scan.created_at < cutoff).delete()
    db.session.commit()
    
    return f"Deleted {deleted} old scans"


@celery.task(name='scanner.cleanup_expired_tokens')
def cleanup_expired_tokens():
    """Scheduled task to clean up expired refresh tokens."""
    from app import db, RefreshToken
    
    deleted = RefreshToken.query.filter(
        RefreshToken.expires_at < datetime.datetime.utcnow()
    ).delete()
    db.session.commit()
    
    return f"Deleted {deleted} expired tokens"


# Scheduled tasks
celery.conf.beat_schedule = {
    'cleanup-old-scans': {
        'task': 'scanner.cleanup_old_scans',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'cleanup-expired-tokens': {
        'task': 'scanner.cleanup_expired_tokens',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}
