import React, { useState, useEffect } from "react";
import "./SiteSecurityAnalyzer.css"; // Import the CSS file

export default function SiteSecurityAnalyzer() {
  const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

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

  const handleScan = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setResult(null);
    setShowDetails(false);
    try {
      const res = await fetch(`${API}/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      setResult(data);
    } catch {
      setResult({ error: "Failed to scan site." });
    } finally {
      setLoading(false);
    }
  };

  const handleAuth = async () => {
    setAuthMessage("");
    if (!email || !password) {
      setAuthMessage("Email and password are required");
      return;
    }
    try {
      const path = authMode === "signup" ? "/auth/signup" : "/auth/login";
      const res = await fetch(`${API}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAuthMessage(data.error || "Auth failed");
        return;
      }
      if (authMode === "login" && data.token) {
        localStorage.setItem("auth_token", data.token);
        setToken(data.token);
        setAuthMessage("Logged in successfully");
      } else if (authMode === "signup") {
        setAuthMessage("Signup successful. You can login now.");
        setAuthMode("login");
      }
    } catch (e) {
      setAuthMessage("Request failed");
    }
  };

  return (
    <div className="analyzer-container">
      <h1 className="title">Site Security Analyzer</h1>

      {/* Auth Panel */}
      <div className="auth-panel" style={{ marginBottom: 20 }}>
        {token ? (
          <div>
            <span style={{ marginRight: 8 }}>Authenticated</span>
            <button onClick={handleLogout}>Logout</button>
          </div>
        ) : (
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <select value={authMode} onChange={(e) => setAuthMode(e.target.value)}>
              <option value="login">Login</option>
              <option value="signup">Signup</option>
            </select>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button onClick={handleAuth}>{authMode === "signup" ? "Create account" : "Login"}</button>
            {authMessage && <span style={{ color: "#e44" }}>{authMessage}</span>}
          </div>
        )}
      </div>

      <div className="input-section">
        <input
          type="text"
          placeholder="Type a website here (e.g. example.com)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button onClick={handleScan} disabled={loading}>
          {loading ? "🔎 Scanning..." : "🔎 Scan"}
        </button>
      </div>

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
