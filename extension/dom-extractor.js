/**
 * Extract visible webpage text.
 * This file is injected only after the user clicks PROTECT ME.
 * It does not run on page load.
 */

function getVisibleText() {
  const clone = document.documentElement.cloneNode(true);

  const scripts = clone.querySelectorAll("script, style, noscript");
  scripts.forEach((el) => el.remove());

  const hidden = clone.querySelectorAll(
    "meta, link, base, head, [hidden], [style*='display: none'], [style*='display:none']"
  );
  hidden.forEach((el) => el.remove());

  const text = clone.innerText || clone.textContent || "";

  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .join("\n");
}

function detectLanguage(text) {
  if (/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]/.test(text)) {
    return "ja";
  }
  if (/[\u4E00-\u9FFF]/.test(text)) {
    return "zh";
  }
  if (/[\uAC00-\uD7AF]/.test(text)) {
    return "ko";
  }
  if (/[\u0600-\u06FF]/.test(text)) {
    return "ar";
  }
  if (/[\u0400-\u04FF]/.test(text)) {
    return "ru";
  }
  if (/[a-zA-Z]/.test(text)) {
    return "en";
  }
  return "unknown";
}

function extractContent() {
  const visibleText = getVisibleText();
  const wordCount = visibleText.split(/\s+/).filter((w) => w.length > 0).length;
  const textPreview = visibleText.substring(0, 300);
  const language = detectLanguage(visibleText);

  return {
    url: window.location.href,
    title: document.title || "(No title)",
    language: language,
    wordCount: wordCount,
    textPreview: textPreview,
    fullText: visibleText,
    timestamp: new Date().toISOString(),
  };
}
