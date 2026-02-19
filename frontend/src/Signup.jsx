import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from './api';

export default function Signup() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [msg, setMsg] = useState('');
    const [msgType, setMsgType] = useState('error');
    const [busy, setBusy] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [passwordStrength, setPasswordStrength] = useState(0);
    const navigate = useNavigate();

    // Check if user is already authenticated on component mount
    useEffect(() => {
        if (api.isAuthenticated()) {
            navigate('/analyze', { replace: true });
        }
    }, [navigate]);

    // Calculate password strength
    useEffect(() => {
        if (!password) {
            setPasswordStrength(0);
            return;
        }
        let strength = 0;
        if (password.length >= 6) strength++;
        if (password.length >= 10) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^a-zA-Z\d]/.test(password)) strength++;
        setPasswordStrength(Math.min(strength, 4));
    }, [password]);

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

        if (password !== confirmPassword) {
            setMsg('Passwords do not match');
            setMsgType('error');
            return;
        }
        if (password.length < 8) {
            setMsg('Password must be at least 8 characters');
            setMsgType('error');
            return;
        }
        // Mirror exact backend validate_password_strength() requirements
        if (!/[A-Z]/.test(password)) {
            setMsg('Password must contain at least one uppercase letter');
            setMsgType('error');
            return;
        }
        if (!/[a-z]/.test(password)) {
            setMsg('Password must contain at least one lowercase letter');
            setMsgType('error');
            return;
        }
        if (!/\d/.test(password)) {
            setMsg('Password must contain at least one number');
            setMsgType('error');
            return;
        }
        setBusy(true);
        setMsg('');
        try {
            await api.post('/auth/signup', { email, password });
            setMsg('✅ Account created! Redirecting to login...');
            setMsgType('success');
            setTimeout(() => {
                navigate('/login');
            }, 1500);
        } catch (e) {
            setMsg(e.message || 'Signup failed. Email might already be registered.');
            setMsgType('error');
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-brutal-green/20 to-brutal-bg dark:from-[#1A1D21] dark:to-[#1A1D21] flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="card-brutal bg-white dark:bg-[#242629] p-8 md:p-10 animate-slide-up">
                    <div className="text-center mb-8">
                        <h1 className="text-4xl font-black font-mono mb-2 dark:text-white">Create Account</h1>
                        <p className="text-brutal-black/60 dark:text-[#8E9297]">Join developers who care about web security</p>
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
                                    minLength={8}
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
                            {password && (
                                <div className="mt-2">
                                    <div className="flex gap-1">
                                        {[1, 2, 3, 4].map((level) => (
                                            <div
                                                key={level}
                                                className={`h-1 flex-1 rounded ${
                                                    passwordStrength >= level
                                                        ? passwordStrength === 1
                                                            ? 'bg-brutal-red'
                                                            : passwordStrength === 2
                                                            ? 'bg-brutal-yellow'
                                                            : passwordStrength === 3
                                                            ? 'bg-brutal-blue'
                                                            : 'bg-brutal-green'
                                                        : 'bg-gray-300 dark:bg-gray-600'
                                                }`}
                                            />
                                        ))}
                                    </div>
                                    <p className="text-xs mt-1 font-mono dark:text-white/70">
                                        Strength: {['', 'Weak', 'Fair', 'Good', 'Strong'][passwordStrength]}
                                    </p>
                                </div>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-bold mb-2 font-mono dark:text-white">CONFIRM PASSWORD</label>
                            <div className="relative">
                                <input
                                    type={showConfirmPassword ? 'text' : 'password'}
                                    className="input-brutal pr-12"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="••••••••"
                                    disabled={busy}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-brutal-black/60 hover:text-brutal-black dark:text-white/60 dark:hover:text-white"
                                    tabIndex="-1"
                                >
                                    {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
                                </button>
                            </div>
                            {confirmPassword && password !== confirmPassword && (
                                <p className="text-xs text-brutal-red mt-1 font-mono">❌ Passwords don't match</p>
                            )}
                            {confirmPassword && password === confirmPassword && (
                                <p className="text-xs text-brutal-green mt-1 font-mono">✅ Passwords match</p>
                            )}
                        </div>

                        {msg && (
                            <div className={`p-3 border-2 border-brutal-black animate-slide-up ${
                                msgType === 'success' 
                                    ? 'bg-brutal-green/20 dark:bg-brutal-green/10' 
                                    : 'bg-brutal-red/20 dark:bg-brutal-red/10'
                            }`}>
                                <p className="text-sm font-bold">{msg}</p>
                            </div>
                        )}

                        <button
                            type="submit"
                            className="w-full btn-brutal bg-brutal-green text-brutal-black py-4 text-lg shadow-brutal-lg hover:shadow-brutal disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            disabled={busy}
                        >
                            {busy ? (
                                <>
                                    <span className="inline-block animate-spin">⚙️</span>
                                    <span>Creating Account...</span>
                                </>
                            ) : (
                                'Create Account'
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-brutal-black/60 dark:text-[#8E9297]">
                            Already have an account?{' '}
                            <Link to="/login" className="font-bold text-brutal-blue hover:underline">
                                Sign in
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
