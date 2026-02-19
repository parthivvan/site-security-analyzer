import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { DarkModeToggle } from './DarkModeContext';
import api from './api';

export default function Header() {
    const location = useLocation();
    const navigate = useNavigate();
    // Use api.isAuthenticated() to check auth status via TokenManager
    const isLoggedIn = api.isAuthenticated();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    /**
     * Handle user logout
     * Uses api.logout() which properly clears all tokens from TokenManager
     * (sessionStorage + localStorage)
     */
    const handleLogout = async () => {
        await api.logout();
        navigate('/');
        window.location.reload();
    };

    const isActive = (path) => location.pathname === path;

    const closeMobileMenu = () => setMobileMenuOpen(false);

    return (
        <header className="bg-white dark:bg-[#1E2124] border-b-3 border-brutal-black dark:border-[#43474D] shadow-brutal dark:shadow-xl sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 py-4">
                <div className="flex justify-between items-center">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-2 group">
                        <div className="text-3xl">🔒</div>
                        <div>
                            <h1 className="text-2xl font-black font-mono tracking-tighter group-hover:text-brutal-blue transition-colors dark:text-white">
                                SITE SECURITY
                            </h1>
                            <p className="text-xs font-mono text-brutal-black/60 dark:text-white/60">ANALYZER v2.0</p>
                        </div>
                    </Link>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center gap-4">
                        <Link
                            to="/analyze"
                            className={`px-4 py-2 font-bold font-mono border-2 border-brutal-black dark:border-white transition-all ${isActive('/analyze')
                                ? 'bg-brutal-yellow shadow-brutal-sm'
                                : 'hover:shadow-brutal-sm hover:translate-x-0.5 hover:translate-y-0.5 dark:text-white'
                                }`}
                        >
                            ANALYZE
                        </Link>
                        <Link
                            to="/learn"
                            className={`px-4 py-2 font-bold font-mono border-2 border-brutal-black dark:border-white transition-all ${isActive('/learn')
                                ? 'bg-brutal-yellow shadow-brutal-sm'
                                : 'hover:shadow-brutal-sm hover:translate-x-0.5 hover:translate-y-0.5 dark:text-white'
                                }`}
                        >
                            LEARN
                        </Link>
                        <Link
                            to="/history"
                            className={`px-4 py-2 font-bold font-mono border-2 border-brutal-black dark:border-white transition-all ${isActive('/history')
                                ? 'bg-brutal-yellow shadow-brutal-sm'
                                : 'hover:shadow-brutal-sm hover:translate-x-0.5 hover:translate-y-0.5 dark:text-white'
                                }`}
                        >
                            HISTORY
                        </Link>
                    </nav>

                    {/* Desktop Auth Buttons + Dark Mode */}
                    <div className="hidden md:flex items-center gap-3">
                        <DarkModeToggle />
                        {isLoggedIn ? (
                            <button
                                onClick={handleLogout}
                                className="px-4 py-2 bg-brutal-red text-white font-bold font-mono border-2 border-brutal-black shadow-brutal hover:shadow-brutal-sm transition-all"
                            >
                                LOGOUT
                            </button>
                        ) : (
                            <>
                                <Link
                                    to="/login"
                                    className="px-4 py-2 font-bold font-mono border-2 border-brutal-black dark:border-[#43474D] dark:text-white hover:shadow-brutal-sm transition-all"
                                >
                                    LOGIN
                                </Link>
                                <Link
                                    to="/signup"
                                    className="px-4 py-2 bg-brutal-green font-bold font-mono border-2 border-brutal-black shadow-brutal hover:shadow-brutal-sm transition-all"
                                >
                                    SIGN UP
                                </Link>
                            </>
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="md:hidden flex items-center gap-3">
                        <DarkModeToggle />
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="p-2 border-2 border-brutal-black dark:border-white bg-white dark:bg-[#1E2124] hover:bg-gray-100 dark:hover:bg-[#242629] transition-colors"
                            aria-label="Toggle menu"
                        >
                            {mobileMenuOpen ? (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            ) : (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>

                {/* Mobile Menu Dropdown */}
                {mobileMenuOpen && (
                    <div className="md:hidden mt-4 pb-4 border-t-2 border-brutal-black dark:border-[#43474D] pt-4 animate-slide-up">
                        <nav className="flex flex-col gap-3">
                            <Link
                                to="/analyze"
                                onClick={closeMobileMenu}
                                className={`px-4 py-3 font-bold font-mono border-2 border-brutal-black dark:border-white transition-all text-center ${isActive('/analyze')
                                    ? 'bg-brutal-yellow'
                                    : 'hover:bg-gray-100 dark:hover:bg-[#242629] dark:text-white'
                                    }`}
                            >
                                ANALYZE
                            </Link>
                            <Link
                                to="/learn"
                                onClick={closeMobileMenu}
                                className={`px-4 py-3 font-bold font-mono border-2 border-brutal-black dark:border-white transition-all text-center ${isActive('/learn')
                                    ? 'bg-brutal-yellow'
                                    : 'hover:bg-gray-100 dark:hover:bg-[#242629] dark:text-white'
                                    }`}
                            >
                                LEARN
                            </Link>
                            <Link
                                to="/history"
                                onClick={closeMobileMenu}
                                className={`px-4 py-3 font-bold font-mono border-2 border-brutal-black dark:border-white transition-all text-center ${isActive('/history')
                                    ? 'bg-brutal-yellow'
                                    : 'hover:bg-gray-100 dark:hover:bg-[#242629] dark:text-white'
                                    }`}
                            >
                                HISTORY
                            </Link>

                            {/* Auth Buttons in Mobile Menu */}
                            <div className="border-t-2 border-brutal-black dark:border-[#43474D] pt-3 mt-2 flex flex-col gap-3">
                                {isLoggedIn ? (
                                    <button
                                        onClick={() => {
                                            handleLogout();
                                            closeMobileMenu();
                                        }}
                                        className="px-4 py-3 bg-brutal-red text-white font-bold font-mono border-2 border-brutal-black shadow-brutal"
                                    >
                                        LOGOUT
                                    </button>
                                ) : (
                                    <>
                                        <Link
                                            to="/login"
                                            onClick={closeMobileMenu}
                                            className="px-4 py-3 font-bold font-mono border-2 border-brutal-black hover:bg-gray-100 dark:hover:bg-[#242629] transition-all text-center dark:text-white"
                                        >
                                            LOGIN
                                        </Link>
                                        <Link
                                            to="/signup"
                                            onClick={closeMobileMenu}
                                            className="px-4 py-3 bg-brutal-green font-bold font-mono border-2 border-brutal-black shadow-brutal text-center"
                                        >
                                            SIGN UP
                                        </Link>
                                    </>
                                )}
                            </div>
                        </nav>
                    </div>
                )}
            </div>
        </header>
    );
}
