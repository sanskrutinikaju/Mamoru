# Mamoru（マモル）

Mamoru is a privacy-first browser safety assistant. It stays inactive until the user clicks **PROTECT ME**, then analyzes the current webpage and returns a Safety Report.

This repository is a college / portfolio project. The architecture is:

```text
Browser Extension → FastAPI → Rule Engine → LLM → Pydantic → Safety Report
```

## Current status

**Milestone 4 — Extension connected to FastAPI** is in place:

- **PROTECT ME** calls `GET /health` on the local backend
- The popup shows the backend reply, or a connection error
- Webpage content is still not collected
- No LLM yet

Later milestones will add the rule engine, LLM analysis, and the Safety Report.

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

Start the backend first, then click the Mamoru icon and **PROTECT ME**. You should see **任せて。** and the health message, then **INACTIVE**. If the backend is stopped, you should see: `Mamoru could not connect to the local safety service.`

After changing `manifest.json`, click **Reload** on the extension card so the new local-host permission is applied.

## Privacy

Mamoru does not scan pages automatically. Analysis happens only after the user explicitly requests it. API keys stay on the backend and must never be placed in the browser extension.
