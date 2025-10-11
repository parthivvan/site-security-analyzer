import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './SiteSecurityAnalyzer.css';
import api from './api';

export default function History(){
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [token, setToken] = useState(null);
  const navigate = useNavigate();

  useEffect(()=>{
    const t = localStorage.getItem('auth_token');
    setToken(t);
    if(!t){
      // redirect if unauthenticated
      navigate('/login');
      return;
    }
    (async ()=>{
      try{
        const data = await api.get('/history', { token: t });
        setItems(data.history || []);
      }catch(e){
        setError(e.message || 'Failed to load history');
      }finally{
        setLoading(false);
      }
    })();
  },[]);

  const logout = () => {
    localStorage.removeItem('auth_token');
    navigate('/login');
  };

  return (
    <div className="analyzer-container">
      <h1 className="title">My Scan History</h1>
      <div className="result-container">
        <div style={{display:'flex', justifyContent:'space-between', marginBottom:12}}>
          <Link to="/analyze" className="btn ghost">Back to Analyze</Link>
          <button className="btn primary" onClick={logout}>Logout</button>
        </div>
        {loading && <p>Loading...</p>}
        {!loading && error && <p className="error-text">{error}</p>}
        {!loading && !error && items.length === 0 && (
          <p className="result-summary">No scans yet. Run a scan from the Analyze page.</p>
        )}
        {!loading && !error && items.length > 0 && (
          <table className="result-table">
            <thead>
              <tr>
                <th>When</th>
                <th>URL</th>
                <th>Status</th>
                <th>HTTPS</th>
                <th>HSTS</th>
                <th>CSP</th>
                <th>Server</th>
                <th>X-Frame-Options</th>
                <th>X-Content-Type-Options</th>
                <th>Referrer-Policy</th>
                <th>Length</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((r, idx)=>{
                const when = r.created_at ? new Date(r.created_at).toLocaleString() : '';
                const rep = r.report || {};
                const rerunUrl = rep.url || r.url;
                const status = rep.status_code ?? '—';
                const non200 = typeof status === 'number' ? status !== 200 : false;
                const badgeCls = non200 ? 'badge badge-warn' : 'badge badge-ok';
                const yesNo = (v) => v ? (<span className="chip-yn ok">Yes</span>) : (<span className="chip-yn no">No</span>);

                return (
                  <tr key={idx}>
                    <td>{when}</td>
                    <td title={rep.final_url || rerunUrl} className="mono">{truncate(rep.final_url || rerunUrl, 64)}</td>
                    <td>
                      <span className={badgeCls}>{String(status)}</span>
                      {non200 && <div className="sub-note">challenge/blocked</div>}
                    </td>
                    <td>{yesNo(!!rep.https)}</td>
                    <td>{yesNo(!!rep.hsts)}</td>
                    <td>{yesNo(!!rep.content_security_policy)}</td>
                    <td>{rep.server_header || '—'}</td>
                    <td>{rep.x_frame_options || '—'}</td>
                    <td>{rep.x_content_type_options || '—'}</td>
                    <td>{rep.referrer_policy || '—'}</td>
                    <td>{rep.content_length ?? '—'}</td>
                    <td className="cell-actions"><Link to={`/analyze?url=${encodeURIComponent(rerunUrl)}`} className="btn ghost">Re-run</Link></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function truncate(str, n){
  if(!str) return '';
  return str.length > n ? str.slice(0, n - 1) + '…' : str;
}
