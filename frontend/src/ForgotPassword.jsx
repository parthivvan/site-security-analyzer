import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from './api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const data = await api.post('/auth/forgot-password', { email: email.toLowerCase().trim() });
      setMessage(data.message || 'If your email is registered, you will receive a password reset link.');
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brutal-red/10 to-brutal-bg dark:from-[#1A1D21] dark:to-[#1A1D21] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="card-brutal bg-white dark:bg-[#242629] p-8 md:p-10 animate-slide-up">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-black font-mono mb-2 dark:text-white">Forgot Password</h1>
            <p className="text-brutal-black/60 dark:text-[#8E9297]">
              Enter your email and we'll send you a reset link
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
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">EMAIL</label>
              <input
                type="email"
                className="input-brutal"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-brutal bg-brutal-black text-white py-4 text-lg shadow-brutal-lg hover:shadow-brutal disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="inline-block animate-spin">⚙️</span>
                  <span>Sending...</span>
                </>
              ) : (
                'Send Reset Link'
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
