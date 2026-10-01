const BACKEND_ANALYZE_URL = "http://127.0.0.1:8000/analyze";
const CONNECT_ERROR = "Mamoru could not connect to the local safety service.";
const EXTRACTION_ERROR = "Could not extract page content. Is this a restricted page?";

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
 * Request content extraction from the content script.
 * Content script has already been injected on all pages.
 */
async function requestContentExtraction() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tab.id, { action: "extractContent" }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(EXTRACTION_ERROR));
        return;
      }
      if (response.success) {
        resolve(response.data);
      } else {
        reject(new Error(response.error || "Unknown extraction error"));
      }
    });
  });
}

/**
 * Display extraction summary and ask for confirmation.
 */
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

/**
 * Send extraction to backend for analysis.
 */
async function sendToBackend(extraction) {
  const response = await fetch(BACKEND_ANALYZE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
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

  if (!response.ok) {
    throw new Error("Backend returned an error.");
  }

  return response.json();
}

/**
 * Main PROTECT ME flow: Extract → Confirm → Send → Complete
 */
protectButton.addEventListener("click", async () => {
  setActive("任せて。");
  showMessage("Extracting page content...", false);

  try {
    // Step 1: Extract content from page
    const extraction = await requestContentExtraction();

    // Step 2: Show summary and ask for confirmation
    displayExtractionSummary(extraction);

    // Step 3: Wait for user confirmation
    return new Promise((resolve) => {
      const confirmBtn = document.getElementById("confirm-button");
      const cancelBtn = document.getElementById("cancel-button");

      confirmBtn.onclick = async () => {
        summaryPanelEl.style.display = "none";
        confirmPanelEl.style.display = "none";
        messageEl.textContent = "Analyzing page...";

        try {
          // Step 4: Send to backend
          const result = await sendToBackend(extraction);

          // Step 5: Show completion
          phraseEl.textContent = "終わった。";
          showMessage(
            result.message || "Mamoru analysis complete.",
            false
          );
        } catch (error) {
          phraseEl.textContent = "注意して。";
          showMessage(CONNECT_ERROR, true);
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
