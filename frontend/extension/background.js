// PhishGuard AI — Background Service Worker
// Handles extension lifecycle events

chrome.runtime.onInstalled.addListener(() => {
  console.log('[PhishGuard] Extension installed.');
});
