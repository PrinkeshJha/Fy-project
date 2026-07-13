// ================================================================
//  PhishGuard AI — Popup Script
//  Handles: URL display, scan button, staged scanning animation,
//           result rendering (safe / phishing / suspicious)
// ================================================================

// ── DOM References ───────────────────────────────────────────────
const scanBtn          = document.getElementById('scanBtn');
const scanText         = document.getElementById('scanText');
const scanIcon         = document.getElementById('scanIcon');
const urlDisplay       = document.getElementById('urlDisplay');
const resultPanel      = document.getElementById('resultPanel');
const resultSafe       = document.getElementById('resultSafe');
const resultDanger     = document.getElementById('resultDanger');
const resultWarning    = document.getElementById('resultWarning');
const confidenceWrap   = document.getElementById('confidenceWrap');
const confidenceFill   = document.getElementById('confidenceFill');
const confidenceScore  = document.getElementById('confidenceScore');
const analysisTags     = document.getElementById('analysisTags');
const scanningOverlay  = document.getElementById('scanningOverlay');
const headerStatus     = document.getElementById('headerStatus');
const step1            = document.getElementById('step1');
const step2            = document.getElementById('step2');
const step3            = document.getElementById('step3');

// ── State ─────────────────────────────────────────────────────────
let currentUrl = '';
let isScanning = false;

// ── Init: Fetch current active tab URL ───────────────────────────
(async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      currentUrl = tab.url;
      urlDisplay.textContent = currentUrl;
    } else {
      urlDisplay.textContent = 'Unable to detect URL';
    }
  } catch (err) {
    urlDisplay.textContent = 'Permission error — check extension settings';
    console.error('[PhishGuard] URL fetch error:', err);
  }
})();

// ── Helpers ───────────────────────────────────────────────────────

/** Update the header status chip */
function setStatus(state, label) {
  const dot   = headerStatus.querySelector('.status-dot');
  const lbl   = headerStatus.querySelector('.status-label');
  dot.className = `status-dot ${state}`;
  lbl.textContent = label;
}

/** Animate scanning steps with delays */
async function runScanSteps() {
  const steps = [step1, step2, step3];

  for (let i = 0; i < steps.length; i++) {
    // Mark current step active
    steps[i].classList.add('active');

    await delay(900 + i * 350);

    // Mark current step done
    steps[i].classList.remove('active');
    steps[i].classList.add('done');
  }
}

/** Simple promise delay helper */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/** Reset scanning step classes */
function resetSteps() {
  [step1, step2, step3].forEach(s => {
    s.classList.remove('active', 'done');
  });
}

/** Hide all result cards */
function hideAllResults() {
  resultSafe.classList.add('hidden');
  resultDanger.classList.add('hidden');
  resultWarning.classList.add('hidden');
  confidenceWrap.classList.add('hidden');
  analysisTags.innerHTML = '';
  analysisTags.classList.add('hidden');
}

/** Render a result card with confidence and tags */
function showResult(verdict, confidence, tags) {
  hideAllResults();

  let card;
  if (verdict === 'safe')    card = resultSafe;
  if (verdict === 'danger')  card = resultDanger;
  if (verdict === 'warning') card = resultWarning;

  if (card) card.classList.remove('hidden');

  // Confidence bar
  confidenceFill.style.width   = '0%';
  confidenceScore.textContent  = '—';
  confidenceWrap.classList.remove('hidden');

  // Animate bar after brief delay (allow DOM repaint)
  requestAnimationFrame(() => {
    setTimeout(() => {
      confidenceFill.style.width  = confidence + '%';
      confidenceScore.textContent = confidence + '%';
    }, 120);
  });

  // Render tags
  if (tags && tags.length) {
    analysisTags.innerHTML = tags
      .map(t => `<span class="tag tag-${t.type}">${t.label}</span>`)
      .join('');
    analysisTags.classList.remove('hidden');
  }
}

// ── Main Scan Handler ─────────────────────────────────────────────
scanBtn.addEventListener('click', async () => {
  if (isScanning) return;
  isScanning = true;

  // Reset previous results
  hideAllResults();

  // Start scanning UI
  scanBtn.disabled = true;
  scanBtn.classList.add('scanning');
  scanText.textContent = 'Scanning...';
  setStatus('scanning', 'Scanning');
  resetSteps();

  // Show overlay
  scanningOverlay.classList.remove('hidden');

  try {
    // Animate scan steps concurrently (visual feedback)
    const stepPromise = runScanSteps();

    // Call real backend API
    const response = await fetch('http://localhost:5000/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: currentUrl })
    });
    
    if (!response.ok) {
      throw new Error(`API returned status: ${response.status}`);
    }
    
    const result = await response.json();

    await stepPromise; // wait for steps to finish before showing result

    // Hide overlay
    scanningOverlay.classList.add('hidden');

    // Show result
    showResult(result.verdict, result.confidence, result.tags);
    setStatus(
      result.verdict === 'danger' ? 'danger' : result.verdict === 'warning' ? 'warning' : 'safe',
      result.verdict === 'danger' ? 'Phishing!' : result.verdict === 'warning' ? 'Suspicious' : 'Safe'
    );

  } catch (err) {
    console.error('[PhishGuard] Scan error:', err);
    scanningOverlay.classList.add('hidden');
    setStatus('danger', 'Error');
  } finally {
    // Restore button
    scanBtn.disabled = false;
    scanBtn.classList.remove('scanning');
    scanText.textContent = 'Scan Again';
    isScanning = false;
  }
});

