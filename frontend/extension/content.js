// PhishGuard AI — Content Script
// Injected into every page; reserved for future screenshot / DOM analysis features.

(function () {
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
    if (request.action === 'getDOMInfo') {
      sendResponse({
        title: document.title,
        url:   window.location.href,
        forms: document.querySelectorAll('form').length,
      });
    }
    return true; // keep channel open for async responses
  });
})();
