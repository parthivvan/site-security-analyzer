// SSA Content Script
// Runs on every page to extract client-side security signals

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scanDOM') {
    const result = {
      insecureForms: 0,
      mixedContent: 0,
      metaTags: 0,
      inlineScripts: 0,
      externalScripts: 0,
    };

    // Count forms that POST to non-HTTPS
    document.querySelectorAll('form').forEach(f => {
      const action = (f.getAttribute('action') || '').trim();
      if (action && action.startsWith('http:')) result.insecureForms++;
    });

    // Count mixed-content resources (http:// on an https page)
    if (location.protocol === 'https:') {
      document.querySelectorAll('img[src^="http:"], script[src^="http:"], link[href^="http:"], iframe[src^="http:"]').forEach(() => {
        result.mixedContent++;
      });
    }

    // Meta tags (CSP meta, referrer, etc.)
    result.metaTags = document.querySelectorAll('meta').length;

    // Inline vs external scripts
    document.querySelectorAll('script').forEach(s => {
      if (s.src) result.externalScripts++;
      else result.inlineScripts++;
    });

    sendResponse(result);
  }
});
