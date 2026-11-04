const BACKEND_ANALYZE_URL = "http://127.0.0.1:8000/analyze";
const CONNECT_ERROR = "Mamoru could not connect to the local safety service.";
const EXTRACTION_ERROR = "Could not extract page content. Is this a restricted page?";
const TOKEN_ERROR =
  "Mamoru is missing its local API token. Copy extension/config.example.js to config.js.";

const statusEl = document.getElementById("status");
const phraseEl = document.getElementById("phrase");
const messageEl = document.getElementById("message");
const protectButton = document.getElementById("protect-me");
const summaryPanelEl = document.getElementById("extraction-summary");
const confirmPanelEl = document.getElementById("extraction-confirm");

function setInactive() {
  statusEl.textContent = "INACTIVE";
  statusEl.classList.remove("active");
  protectButton.disabled = false;
  summaryPanelEl.style.display = "none";
  confirmPanelEl.style.display = "none";
}

function setActive(phrase) {
  statusEl.textContent = "ACTIVE";
  statusEl.classList.add("active");
  phraseEl.textContent = phrase;
  protectButton.disabled = true;
}

function showMessage(text, isError) {
  messageEl.textContent = text;
  messageEl.classList.toggle("error", Boolean(isError));
}

/**
 * Inject the extractor into the current tab only after PROTECT ME.
 * activeTab is granted because the user opened the popup.
 */
async function requestContentExtraction() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || tab.id === undefined) {
    throw new Error(EXTRACTION_ERROR);
  }

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["dom-extractor.js"],
  });

  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => extractContent(),
  });

  const extraction = results && results[0] && results[0].result;
  if (!extraction) {
    throw new Error(EXTRACTION_ERROR);
  }
  return extraction;
}

function displayExtractionSummary(extraction) {
  document.getElementById("summary-url").textContent = extraction.url;
  document.getElementById("summary-title").textContent =
    extraction.title || "(No title)";
  document.getElementById("summary-language").textContent =
    extraction.language.toUpperCase();
  document.getElementById("summary-word-count").textContent =
    extraction.wordCount.toLocaleString();
  document.getElementById("summary-preview").textContent =
    extraction.textPreview || "(No preview available)";

  summaryPanelEl.style.display = "block";
  confirmPanelEl.style.display = "block";
  messageEl.textContent = "Review the extraction summary. Proceed?";
}

async function sendToBackend(extraction) {
  if (typeof MAMORU_API_TOKEN !== "string" || MAMORU_API_TOKEN.length === 0) {
    throw new Error(TOKEN_ERROR);
  }

  const response = await fetch(BACKEND_ANALYZE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Mamoru-Token": MAMORU_API_TOKEN,
    },
    body: JSON.stringify({
      url: extraction.url,
      title: extraction.title,
      language: extraction.language,
      wordCount: extraction.wordCount,
      content: extraction.fullText,
      consentTimestamp: extraction.timestamp,
    }),
  });

  if (response.status === 401 || response.status === 503) {
    throw new Error(TOKEN_ERROR);
  }
  if (!response.ok) {
    throw new Error(CONNECT_ERROR);
  }

  return response.json();
}

protectButton.addEventListener("click", async () => {
  setActive("任せて。");
  showMessage("Extracting page content...", false);

  try {
    const extraction = await requestContentExtraction();
    displayExtractionSummary(extraction);

    return new Promise((resolve) => {
      const confirmBtn = document.getElementById("confirm-button");
      const cancelBtn = document.getElementById("cancel-button");

      confirmBtn.onclick = async () => {
        summaryPanelEl.style.display = "none";
        confirmPanelEl.style.display = "none";
        messageEl.textContent = "Sending to local Mamoru service...";

        try {
          const result = await sendToBackend(extraction);
          phraseEl.textContent = "終わった。";
          showMessage(
            result.message || "Mamoru received the page text.",
            false
          );
        } catch (error) {
          phraseEl.textContent = "注意して。";
          showMessage(error.message || CONNECT_ERROR, true);
        } finally {
          setInactive();
          resolve();
        }
      };

      cancelBtn.onclick = () => {
        summaryPanelEl.style.display = "none";
        confirmPanelEl.style.display = "none";
        showMessage("Analysis cancelled.", false);
        setInactive();
        resolve();
      };
    });
  } catch (error) {
    phraseEl.textContent = "注意して。";
    showMessage(error.message || EXTRACTION_ERROR, true);
    summaryPanelEl.style.display = "none";
    confirmPanelEl.style.display = "none";
    setInactive();
  }
});

setInactive();
