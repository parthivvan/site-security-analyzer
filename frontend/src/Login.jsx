import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from './api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');
  const [msgType, setMsgType] = useState('error'); // 'error' or 'success'
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  // Check if user is already authenticated on component mount
  useEffect(() => {
    if (api.isAuthenticated()) {
      navigate('/analyze', { replace: true });
    }
  }, [navigate]);

  /**
   * Handle login form submission
   * Uses api.login() which properly stores access_token and refresh_token
   * via TokenManager (sessionStorage + localStorage with correct keys)
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setMsg('Email and password are required');
      setMsgType('error');
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setMsg('Please enter a valid email address');
      setMsgType('error');
      return;
    }

    setBusy(true);
    setMsg('');
    try {
      // Use api.login() helper - it handles token storage correctly
      // Backend returns: { access_token, refresh_token, expires_in }
      // api.login() stores them using TokenManager with proper keys
      await api.login(email, password);
      
      setMsg('Login successful! Redirecting...');
      setMsgType('success');
      setTimeout(() => {
        navigate('/analyze', { replace: true });
      }, 500);
    } catch (e) {
      setMsg(e.message || 'Login failed. Please check your credentials.');
      setMsgType('error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brutal-blue/20 to-brutal-bg dark:from-[#1A1D21] dark:to-[#1A1D21] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="card-brutal bg-white dark:bg-[#242629] p-8 md:p-10 animate-slide-up">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-black font-mono mb-2 dark:text-white">Welcome Back</h1>
            <p className="text-brutal-black/60 dark:text-[#8E9297]">Sign in to continue scanning</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">EMAIL</label>
              <input
                type="email"
                className="input-brutal"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                disabled={busy}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">PASSWORD</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input-brutal pr-12"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={busy}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-brutal-black/60 hover:text-brutal-black dark:text-white/60 dark:hover:text-white"
                  tabIndex="-1"
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
            </div>

            {msg && (
              <div className={`p-3 border-2 border-brutal-black animate-slide-up ${msgType === 'success'
                  ? 'bg-brutal-green/20 dark:bg-brutal-green/10'
                  : 'bg-brutal-red/20 dark:bg-brutal-red/10'
                }`}>
                <p className="text-sm font-bold flex items-center gap-2">
                  {msgType === 'success' ? '✅' : '❌'} {msg}
                </p>
              </div>
            )}

            <button
              type="submit"
              className="w-full btn-brutal bg-brutal-black text-white py-4 text-lg shadow-brutal-lg hover:shadow-brutal disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              disabled={busy}
            >
              {busy ? (
                <>
                  <span className="inline-block animate-spin">⚙️</span>
                  <span>Signing In...</span>
                </>
              ) : (
                'Sign In'
              )}
            </button>

            <div className="mt-3 text-center">
              <Link to="/forgot-password" className="text-sm text-brutal-black/70 dark:text-white/70 hover:text-brutal-black dark:hover:text-white font-bold">
                Forgot Password?
              </Link>
            </div>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-brutal-black/60 dark:text-[#8E9297]">
              Don't have an account?{' '}
              <Link to="/signup" className="font-bold text-brutal-blue dark:text-[#5865F2] hover:underline">
                Create one
              </Link>
            </p>
          </div>

          <div className="mt-4 text-center">
            <Link to="/" className="text-sm text-brutal-black/60 dark:text-[#8E9297] hover:text-brutal-black dark:hover:text-white font-medium">
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
