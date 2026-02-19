// Background service worker for Site Security Analyzer Extension
// Handles authentication state and periodic cleanup

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Site Security Analyzer extension installed');
});

// Clean up expired tokens periodically
chrome.alarms.create('cleanup-tokens', { periodInMinutes: 60 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'cleanup-tokens') {
    cleanupExpiredTokens();
  }
});

async function cleanupExpiredTokens() {
  const data = await chrome.storage.local.get(['ssa_token_expiry', 'ssa_access_token']);
  
  if (data.ssa_token_expiry && Date.now() >= parseInt(data.ssa_token_expiry)) {
    // Token expired, remove access token (keep refresh token for renewal)
    await chrome.storage.local.remove('ssa_access_token');
  }
}

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // Validate sender is from this extension
  if (!sender.id || sender.id !== chrome.runtime.id) {
    sendResponse({ error: 'Invalid sender' });
    return;
  }
  
  // Handle message types
  if (request.action === 'get-auth-status') {
    chrome.storage.local.get(['ssa_access_token', 'ssa_refresh_token'], (data) => {
      sendResponse({
        authenticated: !!(data.ssa_access_token && data.ssa_refresh_token)
      });
    });
    return true; // Keep channel open
  }
  
  sendResponse({ success: true });
});
