import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-brutal-bg dark:bg-[#1A1D21] flex items-center justify-center p-4">
      <div className="text-center max-w-lg">
        <div className="text-8xl md:text-9xl font-black font-mono text-brutal-red dark:text-[#ED4245] mb-4">
          404
        </div>
        <h1 className="text-3xl md:text-4xl font-black font-mono mb-4 dark:text-white">
          Page Not Found
        </h1>
        <p className="text-brutal-black/60 dark:text-[#8E9297] mb-8 text-lg">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/"
            className="btn-brutal bg-brutal-black text-white px-8 py-4 text-lg shadow-brutal hover:shadow-brutal-sm transition-all"
          >
            Go Home
          </Link>
          <Link
            to="/analyze"
            className="btn-brutal bg-brutal-blue text-white px-8 py-4 text-lg shadow-brutal hover:shadow-brutal-sm transition-all"
          >
            Start Scanning
          </Link>
        </div>
      </div>
    </div>
  );
}
