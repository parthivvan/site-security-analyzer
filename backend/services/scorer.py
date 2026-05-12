"""
Scoring, flat-report shaping, and remediation engine.

This is the single source of truth for:
  - The flat boolean report contract consumed by the frontend.
  - The numeric security score.
  - Human-readable priority remediation actions.
  - The risk snapshot summary.
"""
from __future__ import annotations

from typing import Any, Dict, List


LABELS = {
    "https": "HTTPS",
    "hsts": "HSTS",
    "content_security_policy": "Content-Security-Policy",
    "x_frame_options": "X-Frame-Options",
    "x_content_type_options": "X-Content-Type-Options",
    "referrer_policy": "Referrer-Policy",
    "permissions_policy": "Permissions-Policy",
    "dns_spf": "SPF",
    "dns_dmarc": "DMARC",
    "server_header": "Server header disclosure",
    "cookies": "Secure cookies",
    "mixed_content": "Mixed content",
}

CHECK_WEIGHTS = {
    "https": 25,
    "hsts": 15,
    "content_security_policy": 15,
    "x_frame_options": 10,
    "x_content_type_options": 5,
    "referrer_policy": 5,
    "permissions_policy": 5,
    "dns_spf": 5,
    "dns_dmarc": 5,
    "cookies": 5,
    "server_header": -5,
    "mixed_content": -5,
}

REMEDIATION_LIBRARY = {
    "https": {
        "severity": "critical",
        "impact": "Traffic can be intercepted or modified in transit.",
        "fix": "Issue a trusted TLS certificate, redirect HTTP to HTTPS, and verify every asset loads over HTTPS.",
        "effort": "Medium",
    },
    "hsts": {
        "severity": "high",
        "impact": "Users can be downgraded to HTTP during first connection or on hostile networks.",
        "fix": "Add Strict-Transport-Security with max-age=31536000; includeSubDomains once subdomains are ready.",
        "effort": "Low",
    },
    "content_security_policy": {
        "severity": "high",
        "impact": "XSS payloads have fewer browser-level restrictions.",
        "fix": "Ship a Content-Security-Policy that starts with default-src 'self' and tight script/style directives.",
        "effort": "Medium",
    },
    "x_frame_options": {
        "severity": "medium",
        "impact": "Pages may be embedded in hostile frames for clickjacking attacks.",
        "fix": "Add X-Frame-Options: DENY or frame-ancestors 'none' in CSP.",
        "effort": "Low",
    },
    "x_content_type_options": {
        "severity": "medium",
        "impact": "Browsers may MIME-sniff files and execute content unexpectedly.",
        "fix": "Add X-Content-Type-Options: nosniff.",
        "effort": "Low",
    },
    "referrer_policy": {
        "severity": "low",
        "impact": "Sensitive paths or query strings may leak to third-party sites.",
        "fix": "Add Referrer-Policy: strict-origin-when-cross-origin or no-referrer for sensitive apps.",
        "effort": "Low",
    },
    "permissions_policy": {
        "severity": "low",
        "impact": "Browser features are not explicitly restricted.",
        "fix": "Add a Permissions-Policy that disables unused sensors, camera, microphone, geolocation, and payment.",
        "effort": "Low",
    },
    "dns_spf": {
        "severity": "medium",
        "impact": "Attackers can spoof mail from this domain more easily.",
        "fix": "Publish an SPF TXT record that lists approved mail senders.",
        "effort": "Medium",
    },
    "dns_dmarc": {
        "severity": "medium",
        "impact": "Spoofed email is harder for receivers to reject or quarantine.",
        "fix": "Publish a DMARC TXT record, start with p=none for monitoring, then move toward quarantine or reject.",
        "effort": "Medium",
    },
    "server_header": {
        "severity": "info",
        "impact": "Infrastructure details can help attackers fingerprint the stack.",
        "fix": "Remove or reduce Server and X-Powered-By headers at the web server or framework layer.",
        "effort": "Low",
    },
    "cookies": {
        "severity": "medium",
        "impact": "Session cookies can be stolen or sent in unsafe contexts.",
        "fix": "Add Secure, HttpOnly, and SameSite attributes to every session or auth cookie.",
        "effort": "Low",
    },
    "mixed_content": {
        "severity": "high",
        "impact": "HTTP resources on an HTTPS page can be modified by attackers.",
        "fix": "Replace HTTP asset, form, and link URLs with HTTPS equivalents.",
        "effort": "Medium",
    },
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


# ── Public API ────────────────────────────────────────────────────────

def grade_for_score(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Moderate"
    return "Critical"


def build_flat_report(
    header_findings: Dict[str, Any],
    dns_findings: Dict[str, Any],
    cookie_findings: Dict[str, Any] | None = None,
    content_findings: Dict[str, Any] | None = None,
) -> Dict[str, bool]:
    """Convert rich scanner findings into the stable flat contract used by the UI."""
    cookie_findings = cookie_findings or {}
    content_findings = content_findings or {}

    hsts = header_findings.get("hsts", {})
    hsts_ok = hsts.get("present", False) and hsts.get("max_age", 0) >= 86400

    csp = header_findings.get("csp", {})
    csp_issues = csp.get("issues", [])
    csp_ok = csp.get("present", False) and not any(
        "unsafe-inline" in issue or "unsafe-eval" in issue or "wildcard" in issue
        for issue in csp_issues
    )

    cookie_data = cookie_findings.get("cookies", {})
    cookies_ok = cookie_data.get("present", False) and not cookie_data.get("issues")

    mixed_content = content_findings.get("mixed_content", {}).get("present", False)

    return {
        "https": header_findings.get("https", {}).get("present", False),
        "hsts": hsts_ok,
        "content_security_policy": csp_ok,
        "x_frame_options": header_findings.get("x_frame_options", {}).get("present", False),
        "x_content_type_options": header_findings.get("x_content_type_options", {}).get("present", False),
        "referrer_policy": header_findings.get("referrer_policy", {}).get("present", False),
        "permissions_policy": header_findings.get("permissions_policy", {}).get("present", False),
        "server_header": header_findings.get("server_disclosure", {}).get("present", False),
        "dns_spf": dns_findings.get("spf", {}).get("present", False),
        "dns_dmarc": dns_findings.get("dmarc", {}).get("present", False),
        "cookies": cookies_ok,
        "mixed_content": mixed_content,
    }


def compute_score_from_flat_report(flat_report: Dict[str, bool]) -> int:
    """Single source of truth for the numeric score."""
    score = 0
    for check, weight in CHECK_WEIGHTS.items():
        if check not in flat_report:
            continue
        value = flat_report[check]
        if weight > 0 and value is True:
            score += weight
        elif weight < 0 and value is True:
            score += weight
    return max(0, min(100, score))


def build_priority_actions(flat_report: Dict[str, bool]) -> List[Dict[str, str]]:
    """Return the most important next fixes, ordered by severity."""
    actions = []
    for key, passed in flat_report.items():
        needs_action = not passed if key != "server_header" else passed
        if not needs_action:
            continue
        item = REMEDIATION_LIBRARY[key]
        actions.append(
            {
                "check": key,
                "title": LABELS[key],
                "severity": item["severity"],
                "impact": item["impact"],
                "fix": item["fix"],
                "effort": item["effort"],
            }
        )
    actions.sort(key=lambda a: SEVERITY_ORDER[a["severity"]])
    return actions[:5]


def build_risk_snapshot(flat_report: Dict[str, bool], score: int) -> Dict[str, Any]:
    actions = build_priority_actions(flat_report)
    critical_or_high = [a for a in actions if a["severity"] in {"critical", "high"}]
    failed = [
        LABELS[key]
        for key, passed in flat_report.items()
        if (not passed and key != "server_header") or (passed and key == "server_header")
    ]

    if score >= 80:
        headline = "Strong baseline with a few hardening opportunities."
    elif critical_or_high:
        headline = "High-value security controls are missing and should be fixed first."
    else:
        headline = "Mostly configuration-level gaps; quick wins can raise the score fast."

    return {
        "grade": grade_for_score(score),
        "headline": headline,
        "failed_checks": failed,
        "critical_or_high_count": len(critical_or_high),
        "quick_win_count": sum(1 for a in actions if a["effort"] == "Low"),
    }


def build_explanation(flat_report: Dict[str, bool], score: int) -> str:
    passed = [LABELS.get(k, k) for k, v in flat_report.items() if k != "server_header" and v]
    failed = [LABELS.get(k, k) for k, v in flat_report.items() if k != "server_header" and not v]
    explanation = (
        f"<strong>Security Grade: {grade_for_score(score)} ({score}/100)</strong><br>"
        f"<strong>Passed ({len(passed)}):</strong> {', '.join(passed) or 'None'}<br>"
        f"<strong>Failed ({len(failed)}):</strong> {', '.join(failed) or 'None'}"
    )
    if flat_report.get("server_header"):
        explanation += " <br><em>Server version is disclosed in response headers.</em>"
    return explanation


def enrich_scan_result(
    result: Dict[str, Any], flat_report: Dict[str, bool], score: int
) -> Dict[str, Any]:
    """Attach portfolio-grade report fields without changing the legacy contract."""
    result["report"] = flat_report
    result["score"] = score
    result["explanation"] = build_explanation(flat_report, score)
    result["priority_actions"] = build_priority_actions(flat_report)
    result["risk_snapshot"] = build_risk_snapshot(flat_report, score)
    return result
