/**
 * TruthLens AI — Extension Popup Logic
 */

const $ = (sel) => document.querySelector(sel);
const show = (el) => el.classList.remove("hidden");
const hide = (el) => el.classList.add("hidden");

const elClaimText = $("#claim-text");
const elBtnVerifyText = $("#btn-verify-text");
const elBtnCapture = $("#btn-capture");
const elBtnVerifySelection = $("#btn-verify-selection");
const elLoading = $("#loading");
const elError = $("#error-msg");
const elResults = $("#results");
const elAiAlert = $("#ai-alert");
const elScoreCircle = $("#score-circle");
const elScoreValue = $("#score-value");
const elCategoryBadge = $("#category-badge");
const elRiskLabel = $("#risk-label");
const elClaimDisplay = $("#claim-text-display");
const elReasonsList = $("#reasons-list");
const elRecommendation = $("#recommendation-text");
const elRecommendationBox = $("#recommendation-box");


// ── Event Listeners ─────────────────────────────────────────────

elBtnVerifyText.addEventListener("click", () => {
    const text = elClaimText.value.trim();
    if (!text) {
        showError("Please enter some text to verify.");
        return;
    }
    verify({ raw_text: text });
});

elBtnCapture.addEventListener("click", () => {
    setLoading(true);
    chrome.runtime.sendMessage({ action: "captureScreenshot" }, (res) => {
        if (res?.success) {
            const base64 = res.dataUrl.split(",")[1];
            verify({ image_base64: base64 });
        } else {
            setLoading(false);
            showError("Failed to capture screenshot.");
        }
    });
});

elBtnVerifySelection.addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs[0]) return showError("No active tab found.");
        chrome.tabs.sendMessage(tabs[0].id, { action: "getSelection" }, (res) => {
            if (chrome.runtime.lastError) {
                showError("Cannot access this page. Try a supported website.");
                return;
            }
            const text = res?.text;
            if (!text) {
                showError("No text selected on the page. Select some text first.");
                return;
            }
            elClaimText.value = text;
            verify({ raw_text: text });
        });
    });
});

// Check for stored result on popup open (from context menu)
chrome.storage.local.get(["lastResult", "lastResultTime"], (data) => {
    if (data.lastResult && data.lastResultTime && Date.now() - data.lastResultTime < 15000) {
        displayResult(data.lastResult);
        chrome.storage.local.remove(["lastResult", "lastResultTime"]);
    }
});


// ── Core Verify Function ────────────────────────────────────────

function verify(payload) {
    hideError();
    hide(elResults);
    setLoading(true);

    // Detect source from active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const url = tabs[0]?.url || "";
        payload.source_app = extractSource(url);

        chrome.runtime.sendMessage({ action: "verify", payload }, (response) => {
            setLoading(false);
            if (response?.success) {
                displayResult(response.data);
            } else {
                showError("Verification failed. Make sure the TruthLens AI backend is running at http://127.0.0.1:8000");
            }
        });
    });
}


// ── Display Result ──────────────────────────────────────────────

function displayResult(data) {
    const score = data.trust_score?.score ?? 0;
    const category = data.trust_score?.category ?? "Unknown";
    const riskLevel = data.trust_score?.risk_level ?? "MEDIUM";
    const claim = data.claim || "—";
    const recommendation = data.recommendation || "—";
    const reasons = data.reasons || [];

    // Score color
    const scoreColor = score <= 25 ? "#ef4444" : score <= 50 ? "#f59e0b" : score <= 75 ? "#06b6d4" : "#10b981";
    const riskColor = riskLevel === "HIGH" ? "#ef4444" : riskLevel === "MEDIUM" ? "#f59e0b" : "#10b981";

    // AI detection
    const mediaAnalysis = (data.detailed_analysis?.media_analysis || "").toLowerCase();
    const isAI = mediaAnalysis.includes("ai-generated") || mediaAnalysis.includes("ai generated") ||
        mediaAnalysis.includes("synthetic") || mediaAnalysis.includes("manipulated") || mediaAnalysis.includes("deepfake");

    if (isAI) {
        show(elAiAlert);
    } else {
        hide(elAiAlert);
    }

    // Score
    elScoreValue.textContent = score;
    elScoreValue.style.color = scoreColor;
    elScoreCircle.style.borderColor = scoreColor;

    // Category
    elCategoryBadge.textContent = category;
    elCategoryBadge.style.color = riskColor;
    elCategoryBadge.style.borderColor = riskColor;

    // Risk
    elRiskLabel.textContent = `Risk: ${riskLevel}`;

    // Claim
    elClaimDisplay.textContent = `"${claim.length > 150 ? claim.substring(0, 150) + '...' : claim}"`;

    // Reasons
    elReasonsList.innerHTML = reasons
        .map(r => `<div class="reason-item-ext">${score <= 50 ? "❌" : "⚠"} ${r}</div>`)
        .join("");

    // Recommendation
    elRecommendation.textContent = recommendation;

    // Risk styling on recommendation box
    if (score <= 25) {
        elRecommendationBox.style.borderLeftColor = "#ef4444";
        elRecommendationBox.style.background = "rgba(239, 68, 68, 0.04)";
    } else if (score <= 75) {
        elRecommendationBox.style.borderLeftColor = "#f59e0b";
        elRecommendationBox.style.background = "rgba(245, 158, 11, 0.04)";
    } else {
        elRecommendationBox.style.borderLeftColor = "#10b981";
        elRecommendationBox.style.background = "rgba(16, 185, 129, 0.04)";
    }

    show(elResults);
}


// ── Helpers ─────────────────────────────────────────────────────

function setLoading(on) {
    if (on) show(elLoading); else hide(elLoading);
    elBtnVerifyText.disabled = on;
    elBtnCapture.disabled = on;
    elBtnVerifySelection.disabled = on;
}

function showError(msg) {
    elError.textContent = msg;
    show(elError);
}

function hideError() {
    hide(elError);
}

function extractSource(url) {
    if (!url) return "Chrome Extension";
    if (url.includes("whatsapp.com")) return "WhatsApp";
    if (url.includes("x.com") || url.includes("twitter.com")) return "Twitter";
    if (url.includes("facebook.com")) return "Facebook";
    if (url.includes("instagram.com")) return "Instagram";
    if (url.includes("youtube.com")) return "YouTube";
    try { return new URL(url).hostname.replace("www.", ""); } catch { return "Chrome Extension"; }
}
