/**
 * DOM Extractor - Content Script
 * Runs in the page context to safely extract visible webpage content.
 * 
 * Privacy: This script runs ONLY when the extension sends a message requesting extraction.
 * No automatic monitoring. No persistent storage. No data collection without user action.
 */

/**
 * Extract visible text from the page.
 * - Removes scripts, styles, comments
 * - Preserves only visible text content
 * - Returns plain text, no HTML
 */
function getVisibleText() {
  // Clone the document to avoid modifying the actual page
  const clone = document.documentElement.cloneNode(true);

  // Remove script and style elements
  const scripts = clone.querySelectorAll("script, style, noscript");
  scripts.forEach((el) => el.remove());

  // Remove common non-content elements
  const hidden = clone.querySelectorAll(
    "meta, link, base, head, [hidden], [style*='display: none'], [style*='display:none']"
  );
  hidden.forEach((el) => el.remove());

  // Get all text content
  const text = clone.innerText || clone.textContent || "";

  // Clean up: remove extra whitespace, normalize line breaks
  const cleaned = text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .join("\n");

  return cleaned;
}

/**
 * Detect language of text using simple heuristics.
 * Returns language code or "unknown".
 */
function detectLanguage(text) {
  // Japanese: Check for Hiragana, Katakana, Kanji
  if (/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]/.test(text)) {
    return "ja";
  }
  // Chinese: Check for CJK unified ideographs
  if (/[\u4E00-\u9FFF]/.test(text)) {
    return "zh";
  }
  // Korean: Check for Hangul
  if (/[\uAC00-\uD7AF]/.test(text)) {
    return "ko";
  }
  // Arabic
  if (/[\u0600-\u06FF]/.test(text)) {
    return "ar";
  }
  // Cyrillic
  if (/[\u0400-\u04FF]/.test(text)) {
    return "ru";
  }
  // Default to English if Latin characters present
  if (/[a-zA-Z]/.test(text)) {
    return "en";
  }
  return "unknown";
}

/**
 * Extract webpage content for analysis.
 * Returns: { url, title, language, wordCount, textPreview, timestamp }
 */
function extractContent() {
  const visibleText = getVisibleText();
  const wordCount = visibleText.split(/\s+/).filter((w) => w.length > 0).length;
  const textPreview = visibleText.substring(0, 300); // First 300 chars
  const language = detectLanguage(visibleText);

  return {
    url: window.location.href,
    title: document.title || "(No title)",
    language: language,
    wordCount: wordCount,
    textPreview: textPreview,
    fullText: visibleText, // Sent only to backend, not logged
    timestamp: new Date().toISOString(),
  };
}

/**
 * Listen for extraction requests from the extension popup.
 * Only responds to requests from the extension itself (content security).
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "extractContent") {
    try {
      const extraction = extractContent();
      sendResponse({
        success: true,
        data: extraction,
      });
    } catch (error) {
      sendResponse({
        success: false,
        error: error.message,
      });
    }
  }
});
