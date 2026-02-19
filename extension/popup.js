// Secure SSA Browser Extension - Popup Script
// Version 2.0 - Production Ready

// DEVELOPMENT: Using localhost
// PRODUCTION: Update these URLs before deploying
const API_URL = 'http://127.0.0.1:5000';    // Backend API
const APP_URL = 'http://localhost:5173';    // Frontend app

console.log('SSA Extension loaded - API:', API_URL);

// Use chrome.storage.local instead of localStorage (more secure)
const storage = {
  async get(key) {
    const result = await chrome.storage.local.get(key);
    return result[key];
  },
  async set(key, value) {
    await chrome.storage.local.set({ [key]: value });
  },
  async remove(key) {
    await chrome.storage.local.remove(key);
  }
};

// ===== Security: Input Validation =====
function sanitizeInput(input) {
  if (typeof input !== 'string') return '';
  return input.replace(/<[^>]*>/g, '').trim();
}

function validateUrl(url) {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

// ===== Dark Mode =====
async function applyTheme() {
  const dark = await storage.get('ssa_dark') === 'true';
  document.documentElement.classList.toggle('dark', dark);
  document.getElementById('themeBtn').textContent = dark ? '☀️' : '🌙';
}

document.getElementById('themeBtn').addEventListener('click', async () => {
  const isDark = document.documentElement.classList.toggle('dark');
  await storage.set('ssa_dark', isDark.toString());
  document.getElementById('themeBtn').textContent = isDark ? '☀️' : '🌙';
});

// ===== Authentication =====
async function getTokens() {
  const accessToken = await storage.get('ssa_access_token');
  const refreshToken = await storage.get('ssa_refresh_token');
  return { accessToken, refreshToken };
}

async function setTokens(accessToken, refreshToken) {
  await storage.set('ssa_access_token', accessToken);
  await storage.set('ssa_refresh_token', refreshToken);
  await storage.set('ssa_token_expiry', Date.now() + 900000); // 15 min
  updateAuthUI();
}

async function clearTokens() {
  await storage.remove('ssa_access_token');
  await storage.remove('ssa_refresh_token');
  await storage.remove('ssa_token_expiry');
  updateAuthUI();
}

async function refreshAccessToken() {
  const { refreshToken } = await getTokens();
  
  if (!refreshToken) {
    throw new Error('No refresh token');
  }
  
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  if (!response.ok) {
    await clearTokens();
    throw new Error('Token refresh failed');
  }
  
  const data = await response.json();
  await setTokens(data.access_token, refreshToken);
  
  return data.access_token;
}

async function updateAuthUI() {
  const { accessToken } = await getTokens();
  
  document.getElementById('authSection').classList.toggle('hidden', !!accessToken);
  document.getElementById('logoutSection').classList.toggle('hidden', !accessToken);
  document.getElementById('scanBtn').disabled = !accessToken;
  
  if (accessToken) {
    try {
      // Safely parse JWT (basic parsing, don't trust payload)
      const parts = accessToken.split('.');
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        const email = sanitizeInput(payload.email || 'Logged in');
        document.getElementById('userEmail').textContent = email;
      }
    } catch {
      document.getElementById('userEmail').textContent = 'Logged in';
    }
  }
}

// ===== Login =====
document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const email = sanitizeInput(document.getElementById('email').value.trim().toLowerCase());
  const password = document.getElementById('password').value;
  const loginErr = document.getElementById('loginError');
  
  loginErr.textContent = '';
  
  if (!email || !password) {
    loginErr.textContent = 'Email & password required';
    return;
  }
  
  // Validate email format
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    loginErr.textContent = 'Invalid email format';
    return;
  }
  
  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }
    
    await setTokens(data.access_token, data.refresh_token);
    
    // Clear password field
    document.getElementById('password').value = '';
    
  } catch (err) {
    loginErr.textContent = sanitizeInput(err.message);
  }
});

document.getElementById('logoutBtn').addEventListener('click', async () => {
  try {
    const { refreshToken } = await getTokens();
    
    // Try to revoke token on server
    await fetch(`${API_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
  } catch (err) {
    console.error('Logout error:', err);
  } finally {
    await clearTokens();
  }
});

// ===== Scanning =====
document.getElementById('scanBtn').addEventListener('click', async () => {
  const statusDiv = document.getElementById('status');
  const resultsDiv = document.getElementById('results');
  const btn = document.getElementById('scanBtn');
  
  statusDiv.innerHTML = '<span class="spinner">⏳</span> Scanning current tab…';
  statusDiv.className = 'status-box';
  btn.disabled = true;
  resultsDiv.classList.add('hidden');
  
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url || !tab.url.startsWith('http')) {
      throw new Error('Cannot scan this page — navigate to a website first.');
    }
    
    // Validate URL
    if (!validateUrl(tab.url)) {
      throw new Error('Invalid URL');
    }
    
    const domain = new URL(tab.url).hostname;
    statusDiv.innerHTML = `<span class="spinner">⏳</span> Analyzing <strong>${sanitizeInput(domain)}</strong>…`;
    
    // Get token (with auto-refresh)
    let { accessToken } = await getTokens();
    const expiry = await storage.get('ssa_token_expiry');
    
    if (!accessToken) {
      throw new Error('Please login first');
    }
    
    // Check if token expired
    if (expiry && Date.now() >= parseInt(expiry)) {
      accessToken = await refreshAccessToken();
    }
    
    // Queue scan
    const response = await fetch(`${API_URL}/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({ url: tab.url })
    });
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.error || `Server error ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.status === 'queued') {
      // Poll for results
      const taskId = data.task_id;
      await pollScanStatus(taskId, domain, accessToken);
    } else if (data.score !== undefined) {
      // Cached result
      displayResults(data, domain);
      statusDiv.innerHTML = '✅ Scan complete (cached)!';
      statusDiv.className = 'status-box status-success';
    } else if (data.error) {
      throw new Error(data.error);
    }
    
  } catch (err) {
    statusDiv.className = 'status-box status-error';
    let msg = `❌ ${sanitizeInput(err.message)}`;
    
    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      msg += '<br><small>Backend not reachable — check configuration</small>';
    }
    
    statusDiv.innerHTML = msg;
  } finally {
    btn.disabled = false;
  }
});

async function pollScanStatus(taskId, domain, accessToken) {
  const statusDiv = document.getElementById('status');
  const maxPolls = 20;
  let polls = 0;
  
  const poll = async () => {
    try {
      const response = await fetch(`${API_URL}/scan/status/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Status check failed');
      }
      
      const data = await response.json();
      
      if (data.status === 'complete') {
        displayResults(data.result, domain);
        statusDiv.innerHTML = '✅ Scan complete!';
        statusDiv.className = 'status-box status-success';
      } else if (data.status === 'failed') {
        throw new Error(data.error || 'Scan failed');
      } else if (polls < maxPolls) {
        polls++;
        const progress = data.progress || 0;
        statusDiv.innerHTML = `<span class="spinner">⏳</span> Scanning... ${progress}%`;
        setTimeout(poll, 2000);  // Poll every 2 seconds
      } else {
        throw new Error('Scan timeout');
      }
    } catch (err) {
      statusDiv.className = 'status-box status-error';
      statusDiv.innerHTML = `❌ ${sanitizeInput(err.message)}`;
    }
  };
  
  poll();
}

function displayResults(data, domain) {
  const resultsDiv = document.getElementById('results');
  const scoreCircle = document.getElementById('scoreCircle');
  const scoreValue = document.getElementById('scoreValue');
  const scoreLabel = document.getElementById('scoreLabel');
  const detailsDiv = document.getElementById('details');
  
  resultsDiv.classList.remove('hidden');
  
  const score = data.score || 0;
  
  // Sanitize and display score
  scoreValue.textContent = `${score}%`;
  scoreCircle.className = 'score-circle';
  
  if (score >= 80) {
    scoreCircle.classList.add('score-excellent');
    scoreLabel.textContent = 'EXCELLENT';
  } else if (score >= 60) {
    scoreCircle.classList.add('score-good');
    scoreLabel.textContent = 'GOOD';
  } else if (score >= 40) {
    scoreCircle.classList.add('score-moderate');
    scoreLabel.textContent = 'MODERATE';
  } else {
    scoreCircle.classList.add('score-critical');
    scoreLabel.textContent = 'CRITICAL';
  }
  
  // Display findings
  const findings = data.findings || {};
  const headers = findings.headers || {};
  
  let html = '';
  
  for (const [key, value] of Object.entries(headers)) {
    if (typeof value === 'object' && value.present !== undefined) {
      const badge = value.severity === 'pass' ? 'badge-pass' : 
                    value.severity === 'critical' || value.severity === 'high' ? 'badge-fail' : 'badge-warn';
      
      html += `
        <div class="detail-row">
          <span class="detail-name">${sanitizeInput(key.toUpperCase())}</span>
          <span class="badge ${badge}">${value.present ? '✓' : '✗'}</span>
        </div>`;
    }
  }
  
  detailsDiv.innerHTML = html;
  
  // Add link to full report (sanitize domain)
  detailsDiv.innerHTML += `
    <a href="${APP_URL}/analyze?url=${encodeURIComponent(sanitizeInput(domain))}" 
       target="_blank" 
       class="detail-link">
      View Full Report in SSA →
    </a>`;
}

// ===== Initialize =====
(async function init() {
  await applyTheme();
  await updateAuthUI();
})();

// Listen for messages from content script (future feature)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // Validate message origin
  if (!sender.tab) {
    sendResponse({ error: 'Invalid origin' });
    return;
  }
  
  // Handle messages securely
  if (request.action === 'scan-page') {
    // Trigger scan
    document.getElementById('scanBtn').click();
  }
  
  sendResponse({ success: true });
});
