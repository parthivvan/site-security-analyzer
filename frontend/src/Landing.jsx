import React from 'react';
import { Link } from 'react-router-dom';
import './SiteSecurityAnalyzer.css';

export default function Landing(){
  return (
    <div className="landing-container">
      <div className="landing-card">
        <h1 className="landing-title">Site Security Analyzer</h1>
        <p className="landing-sub">Check how safe a website is — explained simply.</p>

        <div className="landing-actions">
          <Link to="/analyze" className="btn primary">Start scanning</Link>
          <Link to="/login" className="btn ghost">Login / Signup</Link>
        </div>

        <p className="landing-note">Made friendly for learners — big emoji, simple words, and details when you want them.</p>
      </div>
    </div>
  );
}
