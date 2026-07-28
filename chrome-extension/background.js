/**
 * TruthLens AI — Chrome Extension Background Service Worker
 * Handles context menu, API calls, and tab screenshot capture.
 */

const API_BASE = "http://127.0.0.1:8000";

// ── Context Menu Setup ──────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "truthlens-verify-selection",
        title: "Verify with TruthLens AI",
        contexts: ["selection"],
    });

    chrome.contextMenus.create({
        id: "truthlens-verify-page",
        title: "Verify Page Screenshot with TruthLens",
        contexts: ["page"],
    });

    chrome.contextMenus.create({
        id: "truthlens-verify-image",
        title: "Verify Image with TruthLens",
        contexts: ["image"],
    });
});


// ── Context Menu Click Handlers ─────────────────────────────────

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === "truthlens-verify-selection") {
        const selectedText = info.selectionText;
        if (selectedText) {
            const result = await callVerifyAPI({ raw_text: selectedText, source_app: extractSource(tab.url) });
            sendResultToPopup(result, tab.id);
        }
    }

    if (info.menuItemId === "truthlens-verify-page") {
        try {
            const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "jpeg", quality: 85 });
            const base64 = dataUrl.split(",")[1];
            const result = await callVerifyAPI({ image_base64: base64, source_app: extractSource(tab.url) });
            sendResultToPopup(result, tab.id);
        } catch (e) {
            console.error("Screenshot capture failed:", e);
        }
    }

    if (info.menuItemId === "truthlens-verify-image") {
        // Fetch the image, convert to base64, and verify
        try {
            const response = await fetch(info.srcUrl);
            const blob = await response.blob();
            const base64 = await blobToBase64(blob);
            const result = await callVerifyAPI({ image_base64: base64, source_app: extractSource(tab.url) });
            sendResultToPopup(result, tab.id);
        } catch (e) {
            console.error("Image fetch failed:", e);
        }
    }
});


// ── Message Handler (from popup.js / content.js) ────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "verify") {
        callVerifyAPI(message.payload)
            .then(result => sendResponse({ success: true, data: result }))
            .catch(err => sendResponse({ success: false, error: err.message }));
        return true; // Keep message channel open for async response
    }

    if (message.action === "captureScreenshot") {
        chrome.tabs.captureVisibleTab(null, { format: "jpeg", quality: 85 })
            .then(dataUrl => sendResponse({ success: true, dataUrl }))
            .catch(err => sendResponse({ success: false, error: err.message }));
        return true;
    }

    if (message.action === "getSelectedText") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, { action: "getSelection" }, (response) => {
                    sendResponse(response);
                });
            }
        });
        return true;
    }
});


// ── API Call ─────────────────────────────────────────────────────

async function callVerifyAPI(payload) {
    const response = await fetch(`${API_BASE}/api/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            raw_text: payload.raw_text || null,
            image_base64: payload.image_base64 || null,
            source_app: payload.source_app || "Chrome Extension",
        }),
    });

    if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
    }

    return await response.json();
}


// ── Utilities ───────────────────────────────────────────────────

function extractSource(url) {
    if (!url) return "Unknown";
    if (url.includes("whatsapp.com")) return "WhatsApp";
    if (url.includes("x.com") || url.includes("twitter.com")) return "Twitter";
    if (url.includes("facebook.com")) return "Facebook";
    if (url.includes("instagram.com")) return "Instagram";
    if (url.includes("youtube.com")) return "YouTube";
    return new URL(url).hostname.replace("www.", "");
}

function blobToBase64(blob) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(",")[1]);
        reader.readAsDataURL(blob);
    });
}

function sendResultToPopup(result, tabId) {
    // Store result so popup can read it
    chrome.storage.local.set({ lastResult: result, lastResultTime: Date.now() });
    // Try to send to content script to show inline
    chrome.tabs.sendMessage(tabId, { action: "showResult", data: result }).catch(() => { });
}
