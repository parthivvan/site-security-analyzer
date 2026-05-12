"""Scan routes — submit scan, poll status, sync fallback."""
import json
import logging
import os
import time as _time
from urllib.parse import urlparse

from flask import Blueprint, request, jsonify, g

from config import Config
from extensions import db, limiter, redis_client, REDIS_AVAILABLE
from models.scan import Scan
from routes.auth import auth_required
from services.ssrf_guard import validate_url_safe
from services.scanner import (
    create_safe_session,
    analyze_security_headers,
    analyze_cookies,
    analyze_page_content,
    check_dns_records,
    MAX_RESPONSE_SIZE,
)
from services.scorer import build_flat_report, compute_score_from_flat_report, enrich_scan_result
from utils.helpers import utcnow

logger = logging.getLogger(__name__)

scans_bp = Blueprint("scans", __name__)


@scans_bp.route("/scan", methods=["POST"])
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

    is_valid, normalized_url, error = validate_url_safe(url)
    if not is_valid:
        logger.warning("Invalid URL rejected: %s - %s", url, error)
        return jsonify({"error": error}), 400

    domain = urlparse(normalized_url).hostname

    # Redis cache check
    if REDIS_AVAILABLE:
        cache_key = f"scan:{domain}"
        cached = redis_client.get(cache_key)
        if cached:
            logger.info("Returning cached scan for %s", domain)
            return jsonify(json.loads(cached)), 200

    # ── Async path (Celery) ──────────────────────────────────────────
    if REDIS_AVAILABLE and Config.USE_CELERY:
        try:
            from tasks.scan_tasks import perform_security_scan

            task = perform_security_scan.delay(normalized_url, g.user_id)
            return (
                jsonify(
                    {
                        "task_id": task.id,
                        "status": "queued",
                        "message": "Scan started. Poll /scan/status/<task_id> for results.",
                    }
                ),
                202,
            )
        except Exception as celery_err:
            logger.warning("Celery unavailable (%s), falling back to sync scan", celery_err)

    # ── Synchronous fallback ─────────────────────────────────────────
    logger.info("Running synchronous scan for %s", normalized_url)
    try:
        start_time = _time.time()
        session = create_safe_session()

        with session.get(
            normalized_url, timeout=(5, 10), allow_redirects=True, stream=True
        ) as response:
            content = response.raw.read(MAX_RESPONSE_SIZE + 1, decode_content=True)
            if len(content) > MAX_RESPONSE_SIZE:
                return jsonify({"error": "Response too large"}), 400
            raw_headers = response.headers
            cookie_headers = getattr(response.raw, "headers", response.headers)
            final_url = response.url
            status_code = response.status_code

        header_findings = analyze_security_headers(raw_headers, final_url)
        cookie_findings = analyze_cookies(cookie_headers)
        content_findings = analyze_page_content(content, final_url)
        dns_findings = check_dns_records(domain)

        all_findings = {
            "headers": header_findings,
            "cookies": cookie_findings,
            "dns": dns_findings,
            "content": content_findings,
        }
        flat_report = build_flat_report(header_findings, dns_findings, cookie_findings, content_findings)
        score = compute_score_from_flat_report(flat_report)

        duration_ms = int((_time.time() - start_time) * 1000)

        result = {
            "url": normalized_url,
            "domain": domain,
            "findings": all_findings,
            "final_url": final_url,
            "status_code": status_code,
            "scan_duration_ms": duration_ms,
            "scanned_at": utcnow().isoformat(),
        }
        result = enrich_scan_result(result, flat_report, score)

        # Save to database
        try:
            scan_record = Scan(
                user_id=g.user_id,
                url=normalized_url,
                domain=domain,
                score=score,
                report=json.dumps(flat_report),
                scan_duration_ms=duration_ms,
            )
            db.session.add(scan_record)
            db.session.commit()
            logger.info("Scan saved to DB: %s score=%d", domain, score)
        except Exception as db_err:
            db.session.rollback()
            logger.error("Failed to save scan to DB: %s", db_err)

        return jsonify(result), 200

    except Exception as e:
        logger.error("Sync scan error: %s", e)
        return jsonify({"error": f"Scan failed: {str(e)}"}), 500


@scans_bp.route("/scan/status/<task_id>", methods=["GET"])
@auth_required
def scan_status(task_id):
    """Check status of a queued Celery scan task."""
    if not REDIS_AVAILABLE or not Config.USE_CELERY:
        return (
            jsonify({"status": "failed", "error": "Async scan mode is not enabled on this server"}),
            400,
        )

    try:
        from tasks.scan_tasks import celery_app
        from celery.result import AsyncResult

        task = AsyncResult(task_id, app=celery_app)
        if task.state == "FAILURE":
            return jsonify({"status": "failed", "error": str(task.info)}), 200

        if task.ready():
            result = task.result
            if isinstance(result, dict) and result.get("error"):
                return jsonify({"status": "failed", "error": result["error"]}), 200
            return jsonify({"status": "complete", "result": result}), 200

        progress = task.info.get("progress", 0) if isinstance(task.info, dict) else 0
        stage = task.info.get("stage", "Processing") if isinstance(task.info, dict) else "Processing"
        return jsonify({"status": "processing", "progress": progress, "stage": stage}), 200

    except Exception as e:
        logger.error("Celery status check failed: %s", e)
        return jsonify({"status": "failed", "error": "Could not check task status"}), 500
