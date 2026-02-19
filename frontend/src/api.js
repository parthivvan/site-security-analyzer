/**
 * Secure API Client for Site Security Analyzer
 * 
 * Features:
 * - Automatic token refresh
 * - XSS prevention via input sanitization
 * - Secure token storage strategy
 * - CSRF protection  
 * - Request timeout handling
 */

// In development: leave BASE_URL empty so requests go through the Vite proxy (vite.config.js).
// In production:  set VITE_API_URL to the deployed backend URL (e.g. https://api.yourapp.com).
const BASE_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

// Token management
class TokenManager {
  constructor() {
    this.ACCESS_TOKEN_KEY = 'ssa_access_token';
    this.REFRESH_TOKEN_KEY = 'ssa_refresh_token';
    this.TOKEN_EXPIRY_KEY = 'ssa_token_expiry';
  }

  setTokens(accessToken, refreshToken, expiresIn = 900) {
    // Store in sessionStorage (cleared when tab closes) - more secure than localStorage
    sessionStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);

    // Refresh token in localStorage (needs to persist)
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);

    // Store expiry time
    const expiryTime = Date.now() + (expiresIn * 1000) - 60000; // Refresh 1 min before expiry
    localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime.toString());
  }

  getAccessToken() {
    return sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  getRefreshToken() {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  isTokenExpired() {
    const expiry = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    if (!expiry) return true;
    return Date.now() >= parseInt(expiry);
  }

  clearTokens() {
    sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
  }
}

const tokenManager = new TokenManager();

/**
 * Sanitize user input to prevent XSS
 */
function sanitizeInput(input) {
  if (typeof input !== 'string') return input;

  // Remove any script tags
  let clean = input.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

  // Remove event handlers
  clean = clean.replace(/on\w+\s*=/gi, '');

  // Remove javascript: protocol
  clean = clean.replace(/javascript:/gi, '');

  return clean.trim();
}

/**
 * Validate URL format
 */
function validateUrl(url) {
  try {
    // Sanitize first
    const clean = sanitizeInput(url);

    // Try to parse
    const parsed = new URL(clean.startsWith('http') ? clean : `http://${clean}`);

    // Only allow http/https
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error('Only HTTP/HTTPS protocols allowed');
    }

    // Return just the hostname for safety
    return parsed.hostname;
  } catch (error) {
    throw new Error('Invalid URL format');
  }
}

/**
 * Refresh access token
 */
async function refreshAccessToken() {
  const refreshToken = tokenManager.getRefreshToken();

  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  if (!response.ok) {
    tokenManager.clearTokens();
    throw new Error('Token refresh failed');
  }

  const data = await response.json();
  tokenManager.setTokens(data.access_token, refreshToken, data.expires_in);

  return data.access_token;
}

/**
 * Make authenticated API request
 */
async function request(path, { method = "GET", body, token, skipAuth = false } = {}) {
  const headers = { "Content-Type": "application/json" };

  // Get token
  let accessToken = token;
  if (!skipAuth && !accessToken) {
    // Check if token is expired
    if (tokenManager.isTokenExpired()) {
      try {
        accessToken = await refreshAccessToken();
      } catch (error) {
        // Redirect to login
        window.location.href = '/login';
        throw new Error('Authentication required');
      }
    } else {
      accessToken = tokenManager.getAccessToken();
    }
  }

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  // Add CSRF token if available (for future cookie-based auth)
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  // Make request with timeout
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
      credentials: 'include', // Include cookies
    });

    clearTimeout(timeout);

    let data = null;
    const contentType = res.headers.get('content-type');

    if (contentType && contentType.includes('application/json')) {
      try {
        data = await res.json();
      } catch (e) {
        // JSON parse error
        data = null;
      }
    }

    if (!res.ok) {
      // If 401 and not login endpoint, try to refresh token
      if (res.status === 401 && path !== '/auth/login' && !skipAuth) {
        try {
          const newToken = await refreshAccessToken();
          // Retry request with new token
          return request(path, { method, body, token: newToken });
        } catch (refreshError) {
          // Refresh failed, redirect to login
          tokenManager.clearTokens();
          window.location.href = '/login';
          throw new Error('Authentication required');
        }
      }

      const msg = (data && (data.error || data.message)) || `Request failed: ${res.status}`;
      const err = new Error(msg);
      err.status = res.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (error) {
    clearTimeout(timeout);

    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }

    throw error;
  }
}

// Public API
export const api = {
  get: (path, opts = {}) => request(path, { ...opts, method: "GET" }),
  post: (path, body, opts = {}) => request(path, { ...opts, method: "POST", body }),
  baseUrl: BASE_URL,

  // Auth helpers
  login: async (email, password) => {
    const data = await request('/auth/login', {
      method: 'POST',
      body: { email: sanitizeInput(email), password },
      skipAuth: true
    });

    if (data.access_token && data.refresh_token) {
      tokenManager.setTokens(data.access_token, data.refresh_token, data.expires_in);
    }

    return data;
  },

  logout: async () => {
    try {
      const refreshToken = tokenManager.getRefreshToken();
      await request('/auth/logout', {
        method: 'POST',
        body: { refresh_token: refreshToken }
      });
    } finally {
      tokenManager.clearTokens();
    }
  },

  isAuthenticated: () => {
    return !!tokenManager.getAccessToken() && !!tokenManager.getRefreshToken();
  },

  // Utility functions
  sanitizeInput,
  validateUrl,
  tokenManager
};

export default api;
