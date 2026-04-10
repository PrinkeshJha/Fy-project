// ================================================================
//  PhishGuard AI — Landing Page Script
//
//  This file handles:
//   1. Navbar scroll behaviour
//   2. Mobile hamburger menu
//   3. Scroll-triggered animations
//   4. Stats counter animation
//   5. Fetching live stats from your API  ← main focus
//
// ================================================================


// ──────────────────────────────────────────────────────────────
//  1. NAVBAR — add shadow when user scrolls down
// ──────────────────────────────────────────────────────────────
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 20);
});


// ──────────────────────────────────────────────────────────────
//  2. HAMBURGER — mobile nav toggle
// ──────────────────────────────────────────────────────────────
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('navLinks');
const navCta    = document.getElementById('navCta');

hamburger.addEventListener('click', () => {
  navLinks.classList.toggle('open');
  navCta.classList.toggle('open');
});

// Close mobile nav when a link is clicked
navLinks.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', () => {
    navLinks.classList.remove('open');
    navCta.classList.remove('open');
  });
});


// ──────────────────────────────────────────────────────────────
//  3. SCROLL ANIMATIONS — reveal elements as they enter viewport
// ──────────────────────────────────────────────────────────────
const animatedEls = document.querySelectorAll('[data-animate]');

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;

      const el    = entry.target;
      const delay = parseInt(el.dataset.delay || '0', 10);

      setTimeout(() => {
        el.classList.add('in-view');
      }, delay);

      revealObserver.unobserve(el); // animate only once
    });
  },
  { threshold: 0.15 }
);

animatedEls.forEach(el => revealObserver.observe(el));


// ──────────────────────────────────────────────────────────────
//  4. COUNTER ANIMATION — smoothly count up a number in the DOM
//
//  Usage:  animateCounter(element, targetValue, suffix, duration)
//  e.g.:   animateCounter(el, 10000, '+', 1500)  → "10,000+"
// ──────────────────────────────────────────────────────────────
function animateCounter(el, target, suffix = '', duration = 1400) {
  const start     = performance.now();
  const startVal  = 0;

  function tick(now) {
    const elapsed  = now - start;
    const progress = Math.min(elapsed / duration, 1);

    // Ease-out cubic for natural deceleration
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(startVal + eased * (target - startVal));

    el.textContent = formatNumber(current) + suffix;

    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

// Format: 10000 → "10,000"
function formatNumber(n) {
  return n.toLocaleString('en-IN');
}


// ──────────────────────────────────────────────────────────────
//  5. STATS — FETCH FROM API
//
//  ┌─────────────────────────────────────────────────────────┐
//  │  HOW THE API FETCH PATTERN WORKS                        │
//  │                                                         │
//  │  Step 1: Call fetch() with your backend endpoint URL    │
//  │  Step 2: Await the Response object                      │
//  │  Step 3: Parse JSON from the response body              │
//  │  Step 4: Pull out the fields you need                   │
//  │  Step 5: Update the DOM elements                        │
//  │                                                         │
//  │  If the request fails → fall back to mock/static data   │
//  └─────────────────────────────────────────────────────────┘
//
//  What your backend API should return (JSON example):
//
//  GET /api/stats
//  {
//    "threats_blocked": 12453,    // integer
//    "accuracy":        99.2,     // float (percentage)
//    "avg_scan_time":   1.8,      // float (seconds)
//    "active_users":    3200      // integer
//  }
//
// ──────────────────────────────────────────────────────────────

// ↓ Change this to your backend's URL when ready
const API_BASE_URL = 'https://your-api.com';   // e.g. 'http://localhost:5000'

// DOM references for the stat numbers
const statThreats  = document.getElementById('statThreats');
const statAccuracy = document.getElementById('statAccuracy');
const statScanTime = document.getElementById('statScanTime');
const statUsers    = document.getElementById('statUsers');


async function loadStats() {
  // ── MOCK DATA (used until your real API is ready) ──────────
  //  When your API is live, delete this block and let the real
  //  fetch below take over.
  const MOCK_STATS = {
    threats_blocked: 12453,
    accuracy:        99.2,
    avg_scan_time:   1.8,
    active_users:    3200,
  };

  let stats;

  try {
    // ── STEP 1 & 2: Send request, await response ────────────
    const response = await fetch(`${API_BASE_URL}/api/stats`, {
      method:  'GET',
      headers: { 'Content-Type': 'application/json' },
      // Add auth headers here later if needed:
      // headers: { 'Authorization': `Bearer ${YOUR_TOKEN}` }
    });

    // ── STEP 3: Check HTTP status ───────────────────────────
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    // ── STEP 4: Parse JSON body ─────────────────────────────
    //   response.json() converts the raw response text into a JS object
    stats = await response.json();

    //  At this point `stats` looks like:
    //  { threats_blocked: 12453, accuracy: 99.2, ... }

  } catch (err) {
    // If API call fails (network down, wrong URL, CORS error, etc.)
    // → fall back to mock data so the UI still looks good
    console.warn('[PhishGuard Stats] API unavailable, using mock data.', err.message);
    stats = MOCK_STATS;
  }

  // ── STEP 5: Update the DOM with the stats ─────────────────
  renderStats(stats);
}


function renderStats(stats) {
  // threats_blocked  → e.g. "12,453+"
  animateCounter(statThreats, stats.threats_blocked, '+');

  // accuracy         → e.g. "99.2%"
  //  (accuracy is a float, so we handle it specially)
  animateAccuracy(statAccuracy, stats.accuracy);

  // avg_scan_time    → e.g. "< 2s"
  statScanTime.textContent = `< ${Math.ceil(stats.avg_scan_time)}s`;

  // active_users     → e.g. "3,200+"
  animateCounter(statUsers, stats.active_users, '+');
}


// Special animation for decimal values like 99.2%
function animateAccuracy(el, target, duration = 1400) {
  const start = performance.now();

  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3);
    const current  = (eased * target).toFixed(1);
    el.textContent = current + '%';
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}


// ── Trigger stats load when the stats section enters the viewport
//   (avoids running an animation the user hasn't scrolled to yet)
const statsSection = document.getElementById('stats');

const statsObserver = new IntersectionObserver(
  (entries) => {
    if (entries[0].isIntersecting) {
      loadStats();
      statsObserver.disconnect(); // only load once
    }
  },
  { threshold: 0.3 }
);

statsObserver.observe(statsSection);


// ──────────────────────────────────────────────────────────────
//  HOW TO EXTEND THIS FOR OTHER API DATA
//  ────────────────────────────────────────────────────────────
//
//  The exact same pattern works for any data you want to show:
//
//  async function loadSomeOtherData() {
//    try {
//      const res  = await fetch(`${API_BASE_URL}/api/endpoint`);
//      if (!res.ok) throw new Error(res.statusText);
//      const data = await res.json();          // parse JSON
//      document.getElementById('myEl').textContent = data.someField;
//    } catch (err) {
//      console.error(err);
//    }
//  }
//
//  POST request example (e.g. submitting a URL for analysis):
//
//  async function analyzeUrl(url) {
//    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
//      method: 'POST',
//      headers: { 'Content-Type': 'application/json' },
//      body: JSON.stringify({ url }),     // convert JS object → JSON string
//    });
//    const result = await res.json();    // parse the response
//    console.log(result);                // { verdict: 'safe', confidence: 97 }
//  }
//
// ──────────────────────────────────────────────────────────────
