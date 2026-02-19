import React from 'react';
import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brutal-bg via-brutal-yellow/20 to-brutal-green/20 dark:from-[#1A1D21] dark:via-[#1A1D21] dark:to-[#1A1D21] relative overflow-hidden">
      {/* Animated background shapes */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute w-96 h-96 bg-brutal-yellow/30 dark:bg-blue-500/10 rounded-full blur-3xl -top-48 -left-48 animate-pulse"></div>
        <div className="absolute w-96 h-96 bg-brutal-green/30 dark:bg-emerald-500/10 rounded-full blur-3xl -bottom-48 -right-48 animate-pulse delay-1000"></div>
        <div className="absolute w-64 h-64 bg-brutal-blue/30 dark:bg-yellow-500/10 rounded-full blur-2xl top-1/2 left-1/2 animate-bounce-slow"></div>
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-4 py-12 md:py-20">
        {/* Hero Section */}
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-block mb-6 px-4 py-2 bg-brutal-yellow border-3 border-brutal-black shadow-brutal-sm transform hover:translate-x-1 hover:translate-y-1 hover:shadow-none transition-all">
            <span className="text-sm font-bold font-mono">🔒 SECURITY FIRST</span>
          </div>

          <h1 className="text-6xl md:text-8xl font-black font-mono mb-6 tracking-tighter">
            <span className="text-brutal-black dark:text-white">SITE</span>
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brutal-red via-brutal-blue to-brutal-green animate-gradient">
              SECURITY
            </span>
            <br />
            <span className="text-brutal-black dark:text-white">ANALYZER</span>
          </h1>

          <p className="text-xl md:text-2xl text-brutal-black/80 dark:text-white/70 mb-12 max-w-2xl mx-auto font-medium">
            Analyze any website's security in seconds. Get detailed insights, vulnerability reports, and actionable recommendations.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <Link
              to="/analyze"
              className="btn-brutal bg-brutal-black text-white px-8 py-4 text-lg shadow-brutal-lg hover:shadow-brutal transform hover:-translate-x-1 hover:-translate-y-1 transition-all group"
            >
              <span className="flex items-center gap-2">
                Start Scanning
                <svg className="w-6 h-6 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </span>
            </Link>

            <Link
              to="/login"
              className="btn-brutal bg-white text-brutal-black px-8 py-4 text-lg shadow-brutal hover:shadow-brutal-sm transform hover:translate-x-1 hover:translate-y-1 transition-all"
            >
              Login
            </Link>

            <Link
              to="/signup"
              className="btn-brutal bg-brutal-green text-brutal-black px-8 py-4 text-lg shadow-brutal hover:shadow-brutal-sm transform hover:translate-x-1 hover:translate-y-1 transition-all"
            >
              Sign Up Free
            </Link>
          </div>

          <p className="text-sm text-brutal-black/60 dark:text-white/50">
            No credit card required • Instant results • 100% free
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="card-brutal bg-white dark:bg-[#242629] p-6 transform hover:-translate-y-2 transition-all duration-300 animate-slide-up"
              style={{ animationDelay: `${idx * 100}ms` }}
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-2 font-mono dark:text-white">{feature.title}</h3>
              <p className="text-brutal-black/70 dark:text-white/60">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Stats Section */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16">
          {stats.map((stat, idx) => (
            <div
              key={idx}
              className="card-brutal bg-gradient-to-br from-white to-gray-50 dark:from-[#242629] dark:to-[#1E2124] p-6 text-center transform hover:scale-105 transition-all"
            >
              <div className="text-3xl md:text-4xl font-black font-mono text-brutal-blue dark:text-[#5865F2] mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-brutal-black/70 dark:text-white/60 font-medium">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Final CTA */}
        <div className="card-brutal bg-gradient-to-r from-brutal-yellow to-brutal-green dark:from-[#5865F2] dark:to-[#00D9A3] p-8 md:p-12 text-center">
          <h2 className="text-3xl md:text-5xl font-black font-mono mb-4 dark:text-white">
            Ready to Secure Your Site?
          </h2>
          <p className="text-lg mb-8 text-brutal-black/80 dark:text-white/80">
            Join developers who care about web security
          </p>
          <Link
            to="/analyze"
            className="inline-block btn-brutal bg-brutal-black text-white px-12 py-5 text-xl shadow-brutal-lg hover:shadow-brutal"
          >
            Get Started Now →
          </Link>
        </div>
      </div>
    </div>
  );
}

const features = [
  {
    icon: '🔍',
    title: 'Deep Scanning',
    description: 'Comprehensive security analysis including headers, SSL/TLS, DNS records, and more.'
  },
  {
    icon: '⚡',
    title: 'Lightning Fast',
    description: 'Get results in seconds with our optimized scanning engine.'
  },
  {
    icon: '📊',
    title: 'Detailed Reports',
    description: 'Clear, actionable insights with security scores and exportable reports.'
  },
  {
    icon: '🛡️',
    title: 'OWASP Aligned',
    description: 'Checks based on industry-standard security best practices.'
  },
  {
    icon: '📜',
    title: 'Scan History',
    description: 'Track your security posture over time with persistent scan records.'
  },
  {
    icon: '📚',
    title: 'Learn Security',
    description: 'Built-in educational content to understand every security header.'
  }
];

const stats = [
  { value: '10+', label: 'Security Checks' },
  { value: 'DNS', label: 'SPF & DMARC Analysis' },
  { value: '<2s', label: 'Avg Scan Time' },
  { value: 'Free', label: 'Open Source' }
];
