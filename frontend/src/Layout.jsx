import React, { useEffect, useState } from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import './SiteSecurityAnalyzer.css';
import GlossaryFab from './GlossaryFab.jsx';

export default function Layout(){
  const [token, setToken] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(()=>{
    setToken(localStorage.getItem('auth_token'));
  }, [location.pathname]);

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    navigate('/login');
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="header-inner">
          <Link to="/" className="brand">
            <span className="brand-dot"/> Site Security Analyzer
          </Link>
          <nav className="nav">
            <Link to="/analyze" className="nav-link">Analyze</Link>
            <Link to="/history" className="nav-link">History</Link>
            {token ? (
              <button className="nav-btn" onClick={logout}>Logout</button>
            ) : (
              <Link to="/login" className="nav-link">Login</Link>
            )}
          </nav>
        </div>
      </header>

      <main className="site-main">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="footer-inner">
          <span>© {new Date().getFullYear()} Site Security Analyzer</span>
          <span className="footer-right">Built with Flask + React</span>
        </div>
      </footer>

      <GlossaryFab />
    </div>
  );
}
