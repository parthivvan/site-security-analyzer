"""
Core scanning engine — network fetching and security analysis modules.

This is the actual scanner. It:
1. Creates a safe HTTP session with SSRF-protected adapters.
2. Fetches the target site's headers, cookies, and HTML content.
3. Runs four analysis modules against the collected data.
4. Returns raw findings for the scorer/report-builder to process.
"""
import os
import re
import socket
import ipaddress
import logging
from typing import Dict, Any
from urllib.parse import urlparse

import requests
from urllib3.util.retry import Retry
import dns.resolver

from services.ssrf_guard import SafeHTTPAdapter

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────
SCAN_TIMEOUT = int(os.environ.get("SCAN_TIMEOUT_SECONDS", 30))
MAX_RESPONSE_SIZE = int(os.environ.get("MAX_RESPONSE_SIZE_MB", 10)) * 1024 * 1024
MAX_REDIRECTS = int(os.environ.get("MAX_REDIRECTS", 3))


# ── Session Factory ──────────────────────────────────────────────────

def create_safe_session() -> requests.Session:
    """Create HTTP session with SSRF protection, retries, and safe defaults."""
    session = requests.Session()

    # Use certifi CA bundle so HTTPS works on all platforms
    try:
        import certifi
        session.verify = certifi.where()
    except ImportError:
        pass

    retry_strategy = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )

    session.mount("http://", SafeHTTPAdapter(max_retries=retry_strategy))
    session.mount("https://", SafeHTTPAdapter(max_retries=retry_strategy))

    session.headers.update(
        {
            "User-Agent": "SecurityScanner/2.0 (+https://yourapp.com/about; security@yourapp.com)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
        }
    )
    session.max_redirects = MAX_REDIRECTS
    return session


# ── Analysis Modules ──────────────────────────────────────────────────

def analyze_security_headers(headers, url: str) -> Dict[str, Any]:
    """
    Analyze HTTP response headers for security configuration.

    Accepts any mapping (CaseInsensitiveDict, plain dict, etc.).
    Normalizes to a lowercase-keyed dict internally.
    """
    _h: Dict[str, str] = {}
    for k, v in (headers or {}).items():
        _h[k.lower()] = str(v) if v else ""

    def _get(name: str) -> str:
        return _h.get(name.lower(), "")

    findings = {}

    # HTTPS
    findings["https"] = {
        "present": url.startswith("https://"),
        "score": 15 if url.startswith("https://") else 0,
        "severity": "critical" if not url.startswith("https://") else "pass",
        "details": "HTTPS encrypts traffic"
        if url.startswith("https://")
        else "No HTTPS - traffic can be intercepted",
    }

    # HSTS
    hsts = _get("strict-transport-security")
    if hsts:
        max_age_match = re.search(r"max-age=(\d+)", hsts)
        max_age = int(max_age_match.group(1)) if max_age_match else 0
        has_subdomains = "includeSubDomains" in hsts
        has_preload = "preload" in hsts

        if max_age >= 31536000 and has_subdomains:
            score, severity = 15, "pass"
        elif max_age >= 31536000:
            score, severity = 10, "info"
        elif max_age > 0:
            score, severity = 5, "warning"
        else:
            score, severity = 0, "fail"

        findings["hsts"] = {
            "present": True,
            "value": hsts,
            "max_age": max_age,
            "includeSubDomains": has_subdomains,
            "preload": has_preload,
            "score": score,
            "severity": severity,
            "details": f"HSTS enforces HTTPS for {max_age} seconds",
        }
    else:
        findings["hsts"] = {
            "present": False,
            "score": 0,
            "severity": "critical",
            "details": "Missing HSTS - vulnerable to protocol downgrade attacks",
        }

    # CSP
    csp = _get("content-security-policy")
    if csp:
        issues = []
        if "'unsafe-inline'" in csp:
            issues.append("unsafe-inline allows inline scripts")
        if "'unsafe-eval'" in csp:
            issues.append("unsafe-eval allows eval()")
        if " * " in csp or csp.endswith(" *"):
            issues.append("wildcard (*) allows any source")

        if not issues:
            score, severity = 20, "pass"
        else:
            score, severity = 10, "warning"

        findings["csp"] = {
            "present": True,
            "value": csp[:200] + "..." if len(csp) > 200 else csp,
            "issues": issues,
            "score": score,
            "severity": severity,
            "details": "CSP protects against XSS and injection attacks",
        }
    else:
        findings["csp"] = {
            "present": False,
            "score": 0,
            "severity": "high",
            "details": "Missing CSP - vulnerable to XSS attacks",
        }

    # X-Frame-Options
    xfo = _get("x-frame-options").upper()
    if xfo in ("DENY", "SAMEORIGIN"):
        findings["x_frame_options"] = {
            "present": True,
            "value": xfo,
            "score": 10,
            "severity": "pass",
            "details": f"{xfo} prevents clickjacking",
        }
    elif xfo:
        findings["x_frame_options"] = {
            "present": True,
            "value": xfo,
            "score": 5,
            "severity": "warning",
            "details": "Weak X-Frame-Options value",
        }
    else:
        findings["x_frame_options"] = {
            "present": False,
            "score": 0,
            "severity": "medium",
            "details": "Missing X-Frame-Options - vulnerable to clickjacking",
        }

    # X-Content-Type-Options
    xcto = _get("x-content-type-options").lower()
    findings["x_content_type_options"] = {
        "present": xcto == "nosniff",
        "value": xcto if xcto else None,
        "score": 5 if xcto == "nosniff" else 0,
        "severity": "pass" if xcto == "nosniff" else "medium",
        "details": "Prevents MIME-type sniffing"
        if xcto == "nosniff"
        else "Missing - vulnerable to MIME sniffing",
    }

    # Referrer-Policy
    rp = _get("referrer-policy")
    secure_policies = [
        "no-referrer",
        "same-origin",
        "strict-origin",
        "strict-origin-when-cross-origin",
    ]
    findings["referrer_policy"] = {
        "present": bool(rp),
        "value": rp if rp else None,
        "score": 5 if any(p in rp for p in secure_policies) else 0,
        "severity": "pass" if rp else "low",
        "details": "Controls referrer information leakage"
        if rp
        else "Missing - referrer data may leak",
    }

    # Permissions-Policy / Feature-Policy
    pp = _get("permissions-policy") or _get("feature-policy")
    findings["permissions_policy"] = {
        "present": bool(pp),
        "value": pp[:200] + "..." if len(pp) > 200 else pp,
        "score": 5 if pp else 0,
        "severity": "pass" if pp else "low",
        "details": "Controls browser features"
        if pp
        else "Missing - no control over browser features",
    }

    # X-XSS-Protection (deprecated)
    xxp = _get("x-xss-protection")
    if xxp == "0":
        findings["x_xss_protection"] = {
            "present": True,
            "value": "0",
            "score": 0,
            "severity": "info",
            "details": "Correctly disabled (deprecated header, CSP is better)",
        }
    elif xxp:
        findings["x_xss_protection"] = {
            "present": True,
            "value": xxp,
            "score": -5,
            "severity": "warning",
            "details": "Should be set to 0 or removed (deprecated, can introduce vulnerabilities)",
        }

    # Server Header (info disclosure)
    server = _get("server")
    if server:
        findings["server_disclosure"] = {
            "present": True,
            "value": server,
            "score": -3,
            "severity": "info",
            "details": f"Server version disclosed: {server}",
        }

    # X-Powered-By (info disclosure)
    xpb = _get("x-powered-by")
    if xpb:
        findings["x_powered_by"] = {
            "present": True,
            "value": xpb,
            "score": -3,
            "severity": "info",
            "details": f"Technology stack disclosed: {xpb}",
        }

    return findings


def analyze_cookies(headers) -> Dict[str, Any]:
    """Analyze all Set-Cookie headers for security attributes."""
    if hasattr(headers, "getlist"):
        cookies = headers.getlist("Set-Cookie")
    else:
        raw = headers.get("Set-Cookie", "") if headers else ""
        cookies = [c.strip() for c in raw.split("\n") if c.strip()] if raw else []

    if not cookies:
        return {
            "cookies": {
                "present": False,
                "score": 0,
                "severity": "info",
                "details": "No cookies set - nothing to analyze",
            }
        }

    all_issues = []
    cookie_details = []
    for cookie in cookies:
        issues = []
        lower_cookie = cookie.lower()
        name = cookie.split("=")[0].strip() if "=" in cookie else cookie[:20]

        if "secure" not in lower_cookie:
            issues.append("Missing Secure flag")
        if "httponly" not in lower_cookie:
            issues.append("Missing HttpOnly flag")
        if "samesite" not in lower_cookie:
            issues.append("Missing SameSite attribute")

        all_issues.extend(issues)
        cookie_details.append({"name": name, "issues": issues, "ok": len(issues) == 0})

    unique_issues = sorted(set(all_issues))
    return {
        "cookies": {
            "present": True,
            "cookie_count": len(cookies),
            "cookie_details": cookie_details,
            "issues": unique_issues,
            "score": 0 if unique_issues else 5,
            "severity": "warning" if unique_issues else "pass",
            "details": (
                f"{len(all_issues)} cookie issue(s) across {len(cookies)} cookie(s)"
                if unique_issues
                else f"All {len(cookies)} cookie(s) properly secured"
            ),
        }
    }


def analyze_page_content(content: bytes, final_url: str) -> Dict[str, Any]:
    """Analyze fetched HTML for lightweight client-side security signals."""
    try:
        text = content.decode("utf-8", errors="replace").lower()
    except Exception:
        return {"content_analyzed": False}

    findings: Dict[str, Any] = {"content_analyzed": True}

    if final_url.startswith("https://"):
        mixed = re.findall(r'(?:src|href|action)=["\']http://[^"\']+["\']', text)
        findings["mixed_content"] = {
            "present": len(mixed) > 0,
            "count": len(mixed),
            "score": -5 if mixed else 0,
            "severity": "high" if mixed else "pass",
            "details": (
                f"Found {len(mixed)} mixed content reference(s)"
                if mixed
                else "No mixed content detected"
            ),
        }

    inline_handlers = len(re.findall(r"\bon\w+\s*=\s*[\"']", text))
    findings["inline_event_handlers"] = {
        "count": inline_handlers,
        "score": -3 if inline_handlers > 5 else 0,
        "severity": "info" if inline_handlers > 5 else "pass",
        "details": f"{inline_handlers} inline event handler(s) detected",
    }

    inline_scripts = len(re.findall(r"<script(?:\s[^>]*)?>(?!.*src=)", text))
    findings["inline_scripts"] = {
        "count": inline_scripts,
        "severity": "info",
        "details": f"{inline_scripts} inline script block(s) detected",
    }

    return findings


def check_dns_records(domain: str) -> Dict[str, Any]:
    """Check DNS security records (SPF, DMARC)."""
    findings = {}

    # SPF
    try:
        txt_records = dns.resolver.resolve(domain, "TXT", lifetime=2.0)
        spf_found = False
        spf_record = None

        for rdata in txt_records:
            txt_str = rdata.to_text().strip('"')
            if txt_str.startswith("v=spf1"):
                spf_found = True
                spf_record = txt_str
                break

        findings["spf"] = {
            "present": spf_found,
            "record": spf_record,
            "score": 5 if spf_found else 0,
            "severity": "pass" if spf_found else "medium",
            "details": "SPF protects against email spoofing"
            if spf_found
            else "No SPF record found",
        }
    except Exception as e:
        findings["spf"] = {
            "present": False,
            "score": 0,
            "severity": "medium",
            "details": f"SPF lookup failed: {e}",
        }

    # DMARC
    try:
        dmarc_domain = f"_dmarc.{domain}"
        dmarc_records = dns.resolver.resolve(dmarc_domain, "TXT", lifetime=2.0)
        dmarc_found = False
        dmarc_record = None

        for rdata in dmarc_records:
            txt_str = rdata.to_text().strip('"')
            if txt_str.startswith("v=DMARC1"):
                dmarc_found = True
                dmarc_record = txt_str
                break

        findings["dmarc"] = {
            "present": dmarc_found,
            "record": dmarc_record,
            "score": 5 if dmarc_found else 0,
            "severity": "pass" if dmarc_found else "medium",
            "details": "DMARC provides email authentication"
            if dmarc_found
            else "No DMARC record found",
        }
    except Exception as e:
        findings["dmarc"] = {
            "present": False,
            "score": 0,
            "severity": "medium",
            "details": f"DMARC lookup failed: {e}",
        }

    return findings
