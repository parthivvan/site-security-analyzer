# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)

HISTORY_FILE = "scans.json"

def save_scan(record):
    try:
        data = []
        if os.path.exists(HISTORY_FILE):
            data = json.load(open(HISTORY_FILE))
        data.append(record)
        json.dump(data, open(HISTORY_FILE, "w"), indent=2)
    except Exception as e:
        print("Failed to save:", e)

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

    # new checks
    "hsts": "strict-transport-security" in [h.lower() for h in headers.keys()],
    "content_security_policy": "content-security-policy" in [h.lower() for h in headers.keys()],
    "x_frame_options": headers.get("X-Frame-Options"),
    "x_content_type_options": headers.get("X-Content-Type-Options"),
    "referrer_policy": headers.get("Referrer-Policy"),
}

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # quick human-readable summary (placeholder)
    explanation = []

    # HTTPS check
    if not report["https"]:
        explanation.append("No HTTPS, traffic can be intercepted.")
    else:
        explanation.append("Uses HTTPS.")

# HSTS
    if report["hsts"]:
        explanation.append("Implements HSTS (protects against protocol downgrade).")
    else:
        explanation.append("No HSTS header found.")

# CSP
    if report["content_security_policy"]:
        explanation.append("Content Security Policy is present (helps block XSS).")
    else:
        explanation.append("No CSP header detected (may allow script injection).")

# X-Frame-Options
    if not report["x_frame_options"]:
        explanation.append("Missing X-Frame-Options (site can be iframed).")

# X-Content-Type-Options
    if not report["x_content_type_options"]:
        explanation.append("Missing X-Content-Type-Options (MIME sniffing possible).")

# Referrer Policy
    if not report["referrer_policy"]:
        explanation.append("No Referrer-Policy (referrer data might leak).")

    if report["server_header"]:
        explanation.append(f"Server header reveals: {report['server_header']}.")

    explanation_text = " ".join(explanation)

    out = {"report": report, "explanation": explanation_text}
    save_scan({"url": url, "report": report})
    return jsonify(out)
