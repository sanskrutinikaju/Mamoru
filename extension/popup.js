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
const resultsPanelEl = document.getElementById("analysis-results");

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

function clearFindings() {
  resultsPanelEl.replaceChildren();
  resultsPanelEl.style.display = "none";
}

function appendFindingText(container, className, label, value) {
  const paragraph = document.createElement("p");
  paragraph.className = className;

  const labelEl = document.createElement("strong");
  labelEl.textContent = label;
  const valueEl = document.createElement("span");
  valueEl.textContent = value;

  paragraph.append(labelEl, valueEl);
  container.append(paragraph);
}

function displaySafetyReport(safetyReport, llmStatus, llmMessage) {
  const severityClasses = {
    Low: "low",
    Medium: "medium",
    High: "high",
  };
  const validLevels = ["Low", "Medium", "High", "Cannot tell"];
  const validSources = ["rule", "llm", "rule_and_llm"];
  if (
    !safetyReport ||
    !validLevels.includes(safetyReport.overallLevel) ||
    typeof safetyReport.explanation !== "string" ||
    !Array.isArray(safetyReport.findings) ||
    !["completed", "unavailable", "failed"].includes(llmStatus) ||
    typeof llmMessage !== "string" ||
    !safetyReport.findings.every(
      (finding) =>
        finding &&
        typeof finding.category === "string" &&
        ["Low", "Medium", "High"].includes(finding.severity) &&
        typeof finding.evidence === "string" &&
        typeof finding.explanation === "string" &&
        ["Low", "Medium", "High"].includes(finding.confidence) &&
        validSources.includes(finding.source)
    )
  ) {
    throw new Error("Mamoru received an invalid analysis response.");
  }

  clearFindings();
  const title = document.createElement("h2");
  title.className = "results-title";
  title.textContent = "SAFETY REPORT";
  resultsPanelEl.append(title);

  const overall = document.createElement("p");
  overall.className = `report-level severity-${severityClasses[safetyReport.overallLevel] || "unknown"}`;
  overall.textContent = `Overall level: ${safetyReport.overallLevel}`;
  resultsPanelEl.append(overall);

  const overallExplanation = document.createElement("p");
  overallExplanation.className = "results-note";
  overallExplanation.textContent = safetyReport.explanation;
  resultsPanelEl.append(overallExplanation);

  const note = document.createElement("p");
  note.className = "results-note";
  note.textContent =
    "Signals and confidence are limited indicators, not proof that a page is harmful or safe.";
  resultsPanelEl.append(note);

  if (llmStatus !== "completed") {
    const llmNotice = document.createElement("p");
    llmNotice.className = "results-note";
    llmNotice.textContent = llmMessage;
    resultsPanelEl.append(llmNotice);
  }

  if (safetyReport.overallLevel === "Cannot tell") {
    const emptyState = document.createElement("p");
    emptyState.className = "no-findings";
    emptyState.textContent =
      "Mamoru cannot tell from these results. No findings is not a safety guarantee.";
    resultsPanelEl.append(emptyState);
  }

  safetyReport.findings.forEach((finding) => {
    const card = document.createElement("article");
    card.className = `finding-card severity-${severityClasses[finding.severity]}`;
    appendFindingText(
      card,
      "finding-severity",
      "Severity: ",
      finding.severity
    );
    appendFindingText(
      card,
      "finding-category",
      "Category: ",
      finding.category
    );
    appendFindingText(
      card,
      "finding-description",
      "Explanation: ",
      finding.explanation
    );
    appendFindingText(
      card,
      "finding-confidence",
      "Confidence: ",
      finding.confidence
    );
    appendFindingText(
      card,
      "finding-evidence",
      "Matched text: ",
      finding.evidence
    );
    resultsPanelEl.append(card);
  });

  resultsPanelEl.style.display = "block";
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
  messageEl.textContent = "Review the preview and data-sharing notice. Proceed?";
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
  clearFindings();
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
        messageEl.textContent = "Analyzing with local rules and configured OpenAI...";

        try {
          const result = await sendToBackend(extraction);
          displaySafetyReport(
            result.safetyReport,
            result.llmStatus,
            result.llmMessage
          );
          phraseEl.textContent = "終わった。";
          showMessage("Analysis complete. Review findings below.", false);
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
