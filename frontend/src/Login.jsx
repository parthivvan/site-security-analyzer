import React, {useState} from 'react';
import './SiteSecurityAnalyzer.css';

export default function Login(){
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');

  const handleSubmit = async () => {
    setMsg('Please wait...');
    // keep client-only behavior; real auth happens against backend
    setTimeout(()=>{
      if(mode==='signup') setMsg('Account created. You can login now.');
      else setMsg('Logged in (demo).');
    },700);
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>{mode==='signup' ? 'Create an account' : 'Welcome back'}</h2>
        <p className="muted">Use an email and password to keep your scans saved.</p>

        <div className="form-row">
          <input value={email} onChange={(e)=>setEmail(e.target.value)} placeholder="Email" />
        </div>
        <div className="form-row">
          <input type="password" value={password} onChange={(e)=>setPassword(e.target.value)} placeholder="Password" />
        </div>

        <div className="form-actions">
          <button className="btn primary" onClick={handleSubmit}>{mode==='signup'? 'Create account' : 'Login'}</button>
          <button className="btn ghost" onClick={()=>setMode(mode==='signup'?'login':'signup')}>{mode==='signup' ? 'Switch to login' : 'Create account'}</button>
        </div>

        {msg && <div className="auth-msg">{msg}</div>}
      </div>
    </div>
  );
}
