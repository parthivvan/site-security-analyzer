import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
    return (
        <footer className="bg-brutal-black text-white border-t-3 border-brutal-black mt-auto">
            <div className="max-w-7xl mx-auto px-4 py-8">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    {/* About */}
                    <div>
                        <h3 className="text-lg font-black font-mono mb-3">ABOUT</h3>
                        <p className="text-sm text-white/80">
                            Professional security analysis tool for developers and security enthusiasts.
                        </p>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="text-lg font-black font-mono mb-3">QUICK LINKS</h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <Link to="/analyze" className="text-white/80 hover:text-brutal-yellow transition-colors">
                                    Analyze Site
                                </Link>
                            </li>
                            <li>
                                <Link to="/history" className="text-white/80 hover:text-brutal-yellow transition-colors">
                                    Scan History
                                </Link>
                            </li>
                            <li>
                                <Link to="/login" className="text-white/80 hover:text-brutal-yellow transition-colors">
                                    Login
                                </Link>
                            </li>
                            <li>
                                <Link to="/learn" className="text-white/80 hover:text-brutal-yellow transition-colors">
                                    Learn Security
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Features */}
                    <div>
                        <h3 className="text-lg font-black font-mono mb-3">FEATURES</h3>
                        <ul className="space-y-2 text-sm text-white/80">
                            <li>✓ DNS Security Checks</li>
                            <li>✓ SSL/TLS Analysis</li>
                            <li>✓ Header Inspection</li>
                            <li>✓ SPF & DMARC Analysis</li>
                        </ul>
                    </div>

                    {/* Social */}
                    <div>
                        <h3 className="text-lg font-black font-mono mb-3">CONNECT</h3>
                        <div className="flex gap-3">
                            <a href="https://github.com/ParthivVanapalli" target="_blank" rel="noopener noreferrer" className="w-10 h-10 bg-white text-brutal-black flex items-center justify-center border-2 border-white hover:bg-brutal-yellow transition-colors font-bold">
                                G
                            </a>
                            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="w-10 h-10 bg-white text-brutal-black flex items-center justify-center border-2 border-white hover:bg-brutal-yellow transition-colors font-bold">
                                L
                            </a>
                        </div>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="border-t border-white/20 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-sm text-white/60 font-mono">
                        © 2026 Site Security Analyzer. Built with Flask + React.
                    </p>
                    <div className="flex gap-6 text-sm text-white/60">
                        <Link to="/" className="hover:text-white transition-colors">Home</Link>
                        <Link to="/learn" className="hover:text-white transition-colors">Learn</Link>
                        <a href="https://github.com/ParthivVanapalli" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub</a>
                    </div>
                </div>
            </div>
        </footer>
    );
}
