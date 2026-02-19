import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import api from './api';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const tokenFromUrl = searchParams.get('token');
    if (tokenFromUrl) {
      setToken(tokenFromUrl);
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!token) {
      setError('Reset token is missing');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      await api.post('/auth/reset-password', { token, password });
      setMessage('Password reset successful! Redirecting to login...');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brutal-blue/10 to-brutal-bg dark:from-[#1A1D21] dark:to-[#1A1D21] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="card-brutal bg-white dark:bg-[#242629] p-8 md:p-10 animate-slide-up">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-black font-mono mb-2 dark:text-white">Reset Password</h1>
            <p className="text-brutal-black/60 dark:text-[#8E9297]">
              Enter your new password
            </p>
          </div>

          {error && (
            <div className="p-3 border-2 border-brutal-black dark:border-[#43474D] bg-brutal-red/20 dark:bg-brutal-red/10 mb-4 animate-slide-up">
              <p className="text-sm font-bold flex items-center gap-2">❌ {error}</p>
            </div>
          )}

          {message && (
            <div className="p-3 border-2 border-brutal-black dark:border-[#43474D] bg-brutal-green/20 dark:bg-brutal-green/10 mb-4 animate-slide-up">
              <p className="text-sm font-bold flex items-center gap-2 dark:text-white">✅ {message}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">RESET TOKEN</label>
              <input
                type="text"
                className="input-brutal font-mono text-sm"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
                placeholder="Paste your reset token here"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">NEW PASSWORD</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input-brutal pr-12"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  placeholder="At least 8 characters"
                  disabled={loading}
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

            <div>
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">CONFIRM PASSWORD</label>
              <input
                type="password"
                className="input-brutal"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
                placeholder="Re-enter your password"
                disabled={loading}
              />
              {confirmPassword && password !== confirmPassword && (
                <p className="text-xs text-brutal-red mt-1 font-mono">❌ Passwords don't match</p>
              )}
              {confirmPassword && password === confirmPassword && (
                <p className="text-xs text-brutal-green mt-1 font-mono">✅ Passwords match</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-brutal bg-brutal-black text-white py-4 text-lg shadow-brutal-lg hover:shadow-brutal disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="inline-block animate-spin">⚙️</span>
                  <span>Resetting...</span>
                </>
              ) : (
                'Reset Password'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link to="/login" className="text-sm font-bold text-brutal-blue hover:underline dark:text-[#5865F2]">
              ← Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
