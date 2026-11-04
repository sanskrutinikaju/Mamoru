# Mamoru（マモル）

Mamoru is a consent-first browser threat analyzer. It stays inactive until you click **PROTECT ME**, preview the extracted text, and confirm. Then the extension sends that text to a **local** Python API on your computer.

This is an engineering portfolio project. It is not a finished security product.

## Current status 

**Phase 1 — Hardening** is in place:

- User click → visible text preview → confirm → `POST /analyze`
- Shared secret token + CORS limited to Chrome extension pages
- Size limits and validation that do not echo page text
- Tests and GitHub Actions CI

**Not built yet:** rule engine, LLM, Safety Report, uncertainty handling.

`backend/rules/` still contains leftover keyword files from an older experiment. They are **not** used by the API. Phase 2 will replace that work.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Put the **same** token in `.env` (`MAMORU_API_TOKEN`) and in `extension/config.js`. The example value `dev-only-change-me` is public; change it for any real demo.

## Run the backend

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Health check (no token): [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## Load the extension

1. Open `chrome://extensions` or `edge://extensions`.
2. Turn on **Developer mode**.
3. **Load unpacked** and select the `extension` folder.
4. Click **Reload** after manifest changes.

Then: start the backend → open a normal webpage → click Mamoru → **PROTECT ME** → review preview → **Proceed**.

The backend currently **acknowledges** the text. It does not score threats yet.

## Tests

```powershell
.\scripts\run_tests.ps1
```

Or:

```powershell
$env:MAMORU_API_TOKEN = "test-token-ci"
.\.venv\Scripts\python.exe -m pytest
```

## Privacy

- No scan on page load. The extractor is injected only after **PROTECT ME**.
- Visible text only (not CSS-hidden text, aria-labels, or alt text). See `docs/THREAT_MODEL.md`.
- Page text is not stored. Logs record only HTTP method and path, not bodies.
- API keys must stay in `.env`, never in the extension except the local shared token.

## License

MIT. See `LICENSE`.
