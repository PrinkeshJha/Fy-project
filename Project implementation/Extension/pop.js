// document.addEventListener("DOMContentLoaded", () => {

//     const scanBtn = document.getElementById('scanBtn');

//     scanBtn.addEventListener('click', scanWebsite);

//     // Auto scan when popup opens5
//     scanBtn.click();
// });


// async function scanWebsite() {

//     const statusBadge = document.getElementById('statusBadge');
//     const urlScore = document.getElementById('urlScore');
//     const visualScore = document.getElementById('visualScore');
//     const confidence = document.getElementById('confidence');
//     const scanBtn = document.getElementById('scanBtn');

//     try {
//         // Get active tab safely
//         const tabs = await chrome.tabs.query({ active: true, currentWindow: true });

//         if (!tabs || tabs.length === 0) {
//             throw new Error("No active tab found.");
//         }

//         const url = tabs[0].url;

//         if (!url.startsWith("http")) {
//             throw new Error("This page cannot be scanned.");
//         }

//         // UI → scanning state
//         statusBadge.className = 'status-badge scanning';
//         statusBadge.innerHTML = '<span class="loading"></span> Scanning...';
//         scanBtn.disabled = true;
//         scanBtn.textContent = '⏳ Analyzing...';

//         await delay(1000);

//         // URL analysis
//         const urlAnalysis = analyzeURL(url);
//         urlScore.textContent = urlAnalysis.score + '%';

//         await delay(1000);

//         // Visual analysis (simulated)
//         const visualAnalysis = analyzeVisuals();
//         visualScore.textContent = visualAnalysis.score + '%';

//         // Final result
//         const avgScore = (urlAnalysis.score + visualAnalysis.score) / 2;
//         const isSafe = avgScore > 75;

//         statusBadge.className = 'status-badge ' + (isSafe ? 'safe' : 'suspicious');
//         statusBadge.textContent = isSafe ? '✓ Safe' : '⚠️ Suspicious';
//         confidence.textContent = Math.round(avgScore) + '%';

//     } catch (error) {

//         statusBadge.className = 'status-badge suspicious';
//         statusBadge.textContent = '⚠️ Error';
//         confidence.textContent = '--';
//         console.error(error);

//     } finally {
//         scanBtn.disabled = false;
//         scanBtn.textContent = '🔍 Scan Again';
//     }
// }


// function analyzeURL(url) {

//     let score = 100;

//     try {
//         const parsedURL = new URL(url);
//         const hostname = parsedURL.hostname;
//         const domainParts = hostname.split('.');

//         // HTTPS check
//         if (parsedURL.protocol !== 'https:') score -= 15;

//         // URL length check
//         if (url.length > 75) score -= 10;

//         // Suspicious patterns
//         if (url.includes('@')) score -= 20;

//         if (/\d{1,3}(\.\d{1,3}){3}/.test(hostname)) score -= 15;

//         // Too many subdomains
//         if (domainParts.length > 4) score -= 10;

//     } catch {
//         score -= 30;
//     }

//     return { score: Math.max(score, 30) };
// }


// function analyzeVisuals() {
//     const baseScore = 85 + Math.floor(Math.random() * 15);
//     return { score: baseScore };
// }


// // Clean async delay helper
// function delay(ms) {
//     return new Promise(resolve => setTimeout(resolve, ms));
// }


// -------------------



// http://192.168.1.1/login@com.com -> Example suspicious   


document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("scanBtn").addEventListener("click", scanWebsite);
    document.getElementById("scanBtn").click(); // Auto-scan
});

async function scanWebsite() {

    const statusBadge = document.getElementById('statusBadge');
    const urlScoreEl = document.getElementById('urlScore');
    const visualScoreEl = document.getElementById('visualScore');
    const confidenceEl = document.getElementById('confidence');
    const scanBtn = document.getElementById('scanBtn');

    try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tabs.length) throw new Error("No active tab.");

        const url = tabs[0].url;

        if (!url.startsWith("http")) throw new Error("Unsupported page.");

        updateUI(statusBadge, scanBtn, "Scanning...", "scanning", true);

        await delay(700);

        const urlAnalysis = analyzeURL(url);
        urlScoreEl.textContent = urlAnalysis.score + "%";

        await delay(500);

        const visualScore = simulateVisualScore();
        visualScoreEl.textContent = visualScore + "%";

        const finalScore = Math.round((urlAnalysis.score * 0.7) + (visualScore * 0.3));
        confidenceEl.textContent = finalScore + "%";

        const result = classifyRisk(finalScore);

        statusBadge.className = `status-badge ${result.class}`;
        statusBadge.textContent = result.label;

    } catch (err) {
        statusBadge.className = "status-badge suspicious";
        statusBadge.textContent = "⚠ Error";
        confidenceEl.textContent = "--";
        console.error(err);
    } finally {
        scanBtn.disabled = false;
        scanBtn.textContent = "🔍 Scan Again";
    }
}

/* ------------------------------
   🔍 CORE URL ANALYSIS ENGINE
-------------------------------*/

function analyzeURL(url) {

    let risk = 0;

    try {
        const parsed = new URL(url);
        const hostname = parsed.hostname.toLowerCase();
        const full = url.toLowerCase();

        /* 1️⃣ Protocol */
        if (parsed.protocol !== "https:") risk += 20;

        /* 2️⃣ IP address */
        if (/^\d+\.\d+\.\d+\.\d+$/.test(hostname)) risk += 35;

        /* 3️⃣ Suspicious keywords */
        const keywords = [
            "login","verify","secure","update","account",
            "bank","confirm","password","alert","signin"
        ];
        keywords.forEach(word => {
            if (full.includes(word)) risk += 6;
        });

        /* 4️⃣ Brand impersonation */
        const brands = [
            "amazon","google","facebook","paypal",
            "apple","microsoft","netflix","instagram"
        ];

        brands.forEach(brand => {
            const typo = brand.replace("o", "0");
            if (hostname.includes(typo)) risk += 25;
            if (hostname.includes(brand) && hostname.includes("-")) risk += 15;
        });

        /* 5️⃣ Hyphen abuse */
        const hyphenCount = (hostname.match(/-/g) || []).length;
        if (hyphenCount >= 3) risk += 15;

        /* 6️⃣ Long hostname */
        if (hostname.length > 30) risk += 10;

        /* 7️⃣ Too many subdomains */
        if (hostname.split(".").length > 4) risk += 10;

        /* 8️⃣ URL shorteners */
        const shorteners = [
            "bit.ly","tinyurl","goo.gl","t.co","ow.ly","rb.gy"
        ];
        shorteners.forEach(service => {
            if (hostname.includes(service)) risk += 25;
        });

        /* 9️⃣ @ symbol */
        if (full.includes("@")) risk += 30;

    } catch {
        risk += 40;
    }

    // Convert risk to safe score
    const score = Math.max(100 - risk, 5);

    return { score };
}

/* ------------------------------
   🎨 Simulated Visual AI Score
-------------------------------*/

function simulateVisualScore() {
    return 85 + Math.floor(Math.random() * 10);
}

/* ------------------------------
   🧠 Risk Classification
-------------------------------*/

function classifyRisk(score) {

    if (score >= 85) {
        return { label: "🟢 Safe", class: "safe" };
    }
    else if (score >= 65) {
        return { label: "🟡 Risky", class: "warning" };
    }
    else {
        return { label: "🔴 Phishing", class: "suspicious" };
    }
}

/* ------------------------------
   🔄 UI Helper
-------------------------------*/

function updateUI(badge, btn, text, className, disableBtn) {
    badge.className = `status-badge ${className}`;
    badge.innerHTML = className === "scanning"
        ? `<span class="loading"></span> ${text}`
        : text;

    btn.disabled = disableBtn;
    btn.textContent = disableBtn ? "⏳ Analyzing..." : "🔍 Scan Again";
}

/* ------------------------------
   ⏳ Delay Helper
-------------------------------*/

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
