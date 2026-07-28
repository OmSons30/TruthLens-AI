/**
 * TruthLens AI — Content Script
 * Injects a floating "Verify with TruthLens" button on supported websites
 * and handles inline result display.
 */

(function () {
    // Prevent double injection
    if (document.getElementById("truthlens-fab")) return;

    // ── Floating Action Button ───────────────────────────────────

    const fab = document.createElement("button");
    fab.id = "truthlens-fab";
    fab.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
    <span>Verify</span>
  `;
    fab.title = "Verify with TruthLens AI";
    document.body.appendChild(fab);


    // ── FAB Click Handler ────────────────────────────────────────

    fab.addEventListener("click", async () => {
        const selectedText = window.getSelection().toString().trim();

        if (selectedText) {
            showToast("Analyzing selected text...");
            chrome.runtime.sendMessage(
                { action: "verify", payload: { raw_text: selectedText } },
                (response) => {
                    if (response?.success) {
                        showResultOverlay(response.data);
                    } else {
                        showToast("Verification failed. Is the backend running?", true);
                    }
                }
            );
        } else {
            // Capture screenshot
            showToast("Capturing page screenshot...");
            chrome.runtime.sendMessage(
                { action: "captureScreenshot" },
                (screenshotResponse) => {
                    if (screenshotResponse?.success) {
                        const base64 = screenshotResponse.dataUrl.split(",")[1];
                        chrome.runtime.sendMessage(
                            { action: "verify", payload: { image_base64: base64 } },
                            (response) => {
                                if (response?.success) {
                                    showResultOverlay(response.data);
                                } else {
                                    showToast("Verification failed. Is the backend running?", true);
                                }
                            }
                        );
                    } else {
                        showToast("Screenshot capture failed.", true);
                    }
                }
            );
        }
    });


    // ── Messages from background.js ──────────────────────────────

    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === "getSelection") {
            sendResponse({ text: window.getSelection().toString().trim() });
        }
        if (message.action === "showResult") {
            showResultOverlay(message.data);
        }
    });


    // ── Result Overlay ───────────────────────────────────────────

    function showResultOverlay(data) {
        // Remove existing overlay
        const existing = document.getElementById("truthlens-overlay");
        if (existing) existing.remove();

        const score = data.trust_score?.score ?? 0;
        const category = data.trust_score?.category ?? "Unknown";
        const riskLevel = data.trust_score?.risk_level ?? "MEDIUM";
        const claim = data.claim || "No claim extracted";
        const recommendation = data.recommendation || "";
        const reasons = data.reasons || [];

        const isAI = (() => {
            const notes = (data.detailed_analysis?.media_analysis || "").toLowerCase();
            return notes.includes("ai-generated") || notes.includes("ai generated") ||
                notes.includes("synthetic") || notes.includes("manipulated") || notes.includes("deepfake");
        })();

        const scoreColor = score <= 25 ? "#ef4444" : score <= 50 ? "#f59e0b" : score <= 75 ? "#06b6d4" : "#10b981";
        const riskColor = riskLevel === "HIGH" ? "#ef4444" : riskLevel === "MEDIUM" ? "#f59e0b" : "#10b981";

        const overlay = document.createElement("div");
        overlay.id = "truthlens-overlay";
        overlay.innerHTML = `
      <div class="truthlens-panel">
        <div class="truthlens-panel-header">
          <div class="truthlens-panel-logo">TL</div>
          <strong>TruthLens AI Verdict</strong>
          <button class="truthlens-close" id="truthlens-close-btn">&times;</button>
        </div>

        ${isAI ? `<div class="truthlens-ai-alert">⚠ AI-Generated / Synthetic Content Detected</div>` : ""}

        <div class="truthlens-score-row">
          <div class="truthlens-score-circle" style="border-color: ${scoreColor}">
            <span style="color: ${scoreColor}">${score}</span>
          </div>
          <div class="truthlens-verdict-col">
            <span class="truthlens-category" style="border-color: ${riskColor}; color: ${riskColor}">${category}</span>
            <span class="truthlens-risk">Risk: ${riskLevel}</span>
          </div>
        </div>

        <div class="truthlens-claim">"${claim.length > 120 ? claim.substring(0, 120) + "..." : claim}"</div>

        <div class="truthlens-reasons">
          ${reasons.map(r => `<div class="truthlens-reason">${score <= 50 ? "❌" : "⚠"} ${r}</div>`).join("")}
        </div>

        <div class="truthlens-recommendation">
          <strong>Recommendation:</strong> ${recommendation}
        </div>
      </div>
    `;

        document.body.appendChild(overlay);

        document.getElementById("truthlens-close-btn").addEventListener("click", () => {
            overlay.remove();
        });

        // Close on click outside
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) overlay.remove();
        });
    }


    // ── Toast Notification ────────────────────────────────────────

    function showToast(message, isError = false) {
        const existing = document.getElementById("truthlens-toast");
        if (existing) existing.remove();

        const toast = document.createElement("div");
        toast.id = "truthlens-toast";
        toast.className = isError ? "truthlens-toast-error" : "";
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 3000);
    }
})();
