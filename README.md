# Mamoru（マモル）

Mamoru is a privacy-first browser safety assistant. It stays inactive until the user clicks **PROTECT ME**, then analyzes the current webpage and returns a Safety Report.

This repository is a college / portfolio project. The architecture is:

```text
Browser Extension → FastAPI → Rule Engine → LLM → Pydantic → Safety Report
```

## Current status

**Milestone 5 — Safe Webpage Content Extraction** is complete:

- User clicks **PROTECT ME**
- Extension extracts visible webpage text (user sees preview)
- User confirms extraction before sending
- Backend receives extracted content (NOT stored)
- Backend returns acknowledgement
- Content is ephemeral; never persisted

**Upcoming:** M6 will add the rule engine for deterministic analysis.

## Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Run the backend

```powershell
uvicorn backend.main:app --reload
```

Then open [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) in a browser.

You should see JSON confirming the backend is running.

## Load the browser extension

Chrome or Edge:

1. Open `chrome://extensions` or `edge://extensions`.
2. Turn on **Developer mode**.
3. Click **Load unpacked**.
4. Select the `extension` folder inside this project.

Reload the unpacked extension after code changes.

Start the backend first, then click the Mamoru icon and **PROTECT ME**. 

The extension will:
1. Show **任せて。** (I'm on it)
2. Extract the visible text from the current page
3. Show a summary: URL, title, language, word count, text preview
4. Ask for confirmation: "Proceed with analysis?"
5. Send the extraction to the backend
6. Show **終わった。** (Done) when complete

If the backend is not running, you will see: `Mamoru could not connect to the local safety service.`

After changing `manifest.json`, click **Reload** on the extension card so the new permissions are applied.

## Privacy

Mamoru does not scan pages automatically. Analysis happens only after the user explicitly clicks **PROTECT ME** and confirms the extraction summary.

**Key privacy guarantees (M5):**
- No automatic requests (only on user click)
- No content storage (content processed in memory only)
- No background monitoring (content script runs on demand)
- No browsing history collection (only current page, then deleted)
- No cookies or persistent tracking

**Future milestones** (M6–M10) will add:
- M6: Deterministic rule engine (explicit findings)
- M7: LLM integration (for understanding, not judgment)
- M8: Report generation (findings + reasoning)
- M9: Uncertainty quantification (honest about limitations)
- M10: Privacy controls (user-controlled logging, data export, auto-delete)

