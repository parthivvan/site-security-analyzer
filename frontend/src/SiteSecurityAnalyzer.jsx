import React, { useState, useEffect } from "react";
import { Link, useSearchParams } from 'react-router-dom';
import "./SiteSecurityAnalyzer.css"; // Import the CSS file
import api from "./api";

export default function SiteSecurityAnalyzer() {

  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(null);
  const [authMode, setAuthMode] = useState("login"); // or "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [showDetails, setShowDetails] = useState(false);
  const [eli5, setEli5] = useState(true); // Explain like I'm 5 mode

  useEffect(() => {
    const t = localStorage.getItem("auth_token");
    if (t) setToken(t);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    setToken(null);
  };

  const handleScan = async (overrideUrl) => {
    const target = (overrideUrl ?? url).trim();
    if (!target) {
      setResult({ error: "Please enter a website URL to scan." });
      return;
    }
    setLoading(true);
    setResult(null);
    setShowDetails(false);
    try {
      console.debug("Scanning", { apiBase: api.baseUrl, target });
      const data = await api.post("/scan", { url: target }, { token });
      setResult(data);
    } catch (e) {
      console.error("Scan failed", e);
      setResult({ error: e.message || "Failed to scan site." });
    } finally {
      setLoading(false);
    }
  };

  // If navigated with ?url=..., auto-fill and auto-scan
  const [searchParams] = useSearchParams();
  useEffect(() => {
    const qurl = searchParams.get('url');
    if (qurl) {
      setUrl(qurl);
      // auto-run scan using provided URL
      handleScan(qurl);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAuth = async () => {
    setAuthMessage("");
    if (!email || !password) {
      setAuthMessage("Email and password are required");
      return;
    }
    try {
      const path = authMode === "signup" ? "/auth/signup" : "/auth/login";
      const data = await api.post(path, { email, password });
      if (authMode === "login" && data?.token) {
        localStorage.setItem("auth_token", data.token);
        setToken(data.token);
        setAuthMessage("Logged in successfully");
      } else if (authMode === "signup") {
        setAuthMessage("Signup successful. You can login now.");
        setAuthMode("login");
      } else {
        setAuthMessage("Auth succeeded");
      }
    } catch (e) {
      setAuthMessage(e.message || "Request failed");
    }
  };

  return (
    <div className="analyzer-container">
      <h1 className="title">Site Security Analyzer</h1>

      <form className="input-section" onSubmit={(e)=>{ e.preventDefault(); if(!loading && url.trim()){ handleScan(); } }}>
        <input
          type="text"
          placeholder="Type a website here (e.g. example.com)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button type="submit" disabled={loading || !url.trim()}>
          {loading ? "🔎 Scanning..." : "🔎 Scan"}
        </button>
      </form>

      {/* Friendly small controls */}
      <div className="kid-controls">
        <label>
          <input type="checkbox" checked={eli5} onChange={(e) => setEli5(e.target.checked)} />
          Explain like I'm 5 (simple words)
        </label>
        <button className="details-toggle" onClick={() => setShowDetails((s) => !s)}>
          {showDetails ? "Hide details" : "Show details"}
        </button>
      </div>

      {result && (
        <div className="result-container">
          {result.error ? (
            <p className="error-text">{result.error}</p>
          ) : (
            <>
              {/* Actions row */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
                <Link to="/history" className="btn ghost">View history</Link>
              </div>
              {/* Friendly summary with emoji and simple language when ELI5 is on */}
              <div className="kid-summary">
                <div className="kid-emoji">{result.report && result.report.https ? "🟢" : "🔴"}</div>
                <div className="kid-text">
                  {eli5 ? (
                    <p>
                      I looked at <strong>{result.report?.url}</strong>. {result.explanation}
                    </p>
                  ) : (
                    <p className="result-summary">{result.explanation}</p>
                  )}
                </div>
              </div>

              {/* Simple animated progress / score bar for kids */}
              <div className="score-row">
                <div className="score-label">Safety score</div>
                <div className="score-bar">
                  <div
                    className={`score-fill ${result.report?.https ? 'good' : 'bad'}`}
                    style={{ width: `${calculateScore(result.report)}%` }}
                  />
                </div>
                <div className="score-number">{calculateScore(result.report)}%</div>
              </div>

              {/* Detailed table hidden behind a toggle so kids see simple info first */}
              {showDetails && (
                <table className="result-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(result.report).map(([key, value], idx) => (
                      <tr key={idx}>
                        <td>{key.replaceAll("_", " ")}</td>
                        <td>{String(value) || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// Tiny helper to compute a kid-friendly score based on a few booleans
function calculateScore(report) {
  if (!report) return 0;
  let score = 50; // start neutral
  if (report.https) score += 30;
  if (report.hsts) score += 10;
  if (report.content_security_policy) score += 10;
  if (!report.x_frame_options) score -= 10;
  if (!report.x_content_type_options) score -= 10;
  if (!report.referrer_policy) score -= 5;
  if (score < 0) score = 0;
  if (score > 100) score = 100;
  return Math.round(score);
}
