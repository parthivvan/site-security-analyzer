import React, {useState} from 'react';
import './SiteSecurityAnalyzer.css';
import api from './api';
import { useNavigate, useLocation } from 'react-router-dom';

export default function Login(){
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/analyze';
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async () => {
    if(!email || !password){
      setMsg('Email and password are required');
      return;
    }
    setBusy(true);
    setMsg('Please wait...');
    try{
      const path = mode === 'signup' ? '/auth/signup' : '/auth/login';
      const data = await api.post(path, { email, password });
      if(mode === 'signup'){
        setMsg('Account created. You can login now.');
        setMode('login');
      } else {
        if(data && data.token){
          localStorage.setItem('auth_token', data.token);
          setMsg('Logged in successfully');
          navigate(from, { replace: true });
        } else {
          setMsg('Login succeeded, but token missing');
        }
      }
    }catch(e){
      setMsg(e.message || 'Request failed');
    }finally{
      setBusy(false);
    }
  };

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
          <button disabled={busy} className="btn primary" onClick={handleSubmit}>{mode==='signup'? 'Create account' : 'Login'}</button>
          <button disabled={busy} className="btn ghost" onClick={()=>setMode(mode==='signup'?'login':'signup')}>{mode==='signup' ? 'Switch to login' : 'Create account'}</button>
        </div>

        {msg && <div className="auth-msg">{msg}</div>}
      </div>
    </div>
  );
}
