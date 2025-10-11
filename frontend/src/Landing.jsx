import React from 'react';
import { Link } from 'react-router-dom';
import './SiteSecurityAnalyzer.css';

export default function Landing(){
  return (
    <div className="landing-container">
      <div className="landing-card">
        <div className="orbs">
          <div className="orb o1"/>
          <div className="orb o2"/>
          <div className="orb o3"/>
        </div>
        <h1 className="landing-title">Site Security Analyzer</h1>
        <div className="landing-hero-line"/>
        <p className="landing-sub">Check how safe a website is — explained simply.</p>

        <div className="landing-actions">
          <Link to="/analyze" className="btn primary">Start scanning</Link>
          <Link to="/login" className="btn ghost">Login / Signup</Link>
          <Link to="/history" className="btn ghost">My history</Link>
        </div>

        <div className="landing-features">
          <span className="chip">Security headers insight</span>
          <span className="chip">HSTS & CSP detection</span>
          <span className="chip">Simple explanations</span>
          <span className="chip">Private by design</span>
        </div>

        <p className="landing-note">Made friendly for learners — big emoji, simple words, and details when you want them.</p>
      </div>
    </div>
  );
}
