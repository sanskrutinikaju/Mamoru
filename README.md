# Mamoru（マモル）

Mamoru is a consent-first browser threat analyzer. It stays inactive until you click **PROTECT ME**, preview the extracted text, and confirm. Then the extension sends that text to a **local** Python API on your computer.

This is an engineering portfolio project. It is not a finished security product.

## Current status 

**Phase 5 — Evaluation harness** is implemented; live LLM measurements require a locally configured API key:

- User click → visible text preview → confirm → `POST /analyze`
- Shared secret token + CORS limited to the configured extension origin
- Character and request-body size limits, plus validation that does not echo page text
- Deterministic rules return severity, category, description, and matched text evidence
- One OpenAI provider returns validated, structured findings in addition to the deterministic rules
- A Safety Report summarizes severity, evidence, explanation, confidence, and a **Cannot tell** outcome
- The extension displays the report as plain text; findings are signals, not proof
- Provider errors return deterministic findings with an explicit fallback status
- A 120-case synthetic dataset has a fixed 24-case held-out split for evaluation
- The evaluator compares rules-only, LLM-only, and hybrid results without tuning on held-out examples

**Not built yet:** agentic investigation and production packaging.

The current rules flag credential requests, urgency pressure, prompt-injection phrases, and suspicious link wording. Link checks use visible text only; they cannot compare displayed link text with its actual destination. A missing match does not mean a page is safe.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Load the unpacked extension as described below, then open `chrome://extensions` and copy Mamoru's extension ID. In `.env`, set `MAMORU_EXTENSION_ORIGIN` to `chrome-extension://` followed by that exact ID. This exact match restricts browser access to your copy of Mamoru; leaving it blank disables browser-origin access.

Generate a unique local token and put the same value in `.env` (`MAMORU_API_TOKEN`) and `extension/config.js`. The example value `dev-only-change-me` is public; never use it for a real demo. The token is stored in the local extension files so the extension can send it; it does not protect against another program running as you or someone who can read those files.

Set `OPENAI_API_KEY` in `.env` to enable LLM analysis. The key stays in the backend process and is never placed in the extension. The default model is `gpt-4o-mini`; you can set `OPENAI_MODEL` in `.env` to choose another supported model. Without a key, the API reports that LLM analysis is unavailable and returns deterministic rule findings only.

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

After setting the extension origin and token, restart the backend. Then open a normal webpage → click Mamoru → **PROTECT ME** → review the displayed preview and data-sharing notice → **Proceed**. The preview shows only the first 300 characters; proceeding sends the full extracted visible text to the local backend. If configured, the backend sends only the first 12,000 characters to OpenAI. The URL and page title are not sent to OpenAI.

The backend runs deterministic text rules and OpenAI analysis. Deterministic findings remain in the response even if the LLM is unavailable or fails. Rules set a minimum severity that the LLM cannot lower. Rules and LLM output are limited signals, not a complete threat detector or proof of harm. Text sent to OpenAI is subject to the provider's privacy and retention terms.

The Safety Report uses the strongest finding severity; when no finding is returned it says **Cannot tell**, not Low or safe. Confidence labels describe agreement between the rule and LLM sources, not a probability. See [SAFETY_REPORT.md](<C:/Users/sanskruti  Nikaju/Documents/Mamoru/docs/SAFETY_REPORT.md>) for meanings, thresholds, and the synthetic High-versus-Medium check.

## Tests

```powershell
.\scripts\run_tests.ps1
```

Or:

```powershell
$env:MAMORU_API_TOKEN = "test-token-ci"
.\.venv\Scripts\python.exe -m pytest
```

## Rule evaluation

Run offline rules-only metrics on the held-out cases with:

```powershell
.\.venv\Scripts\python.exe eval\run.py --rules-only
```

To compare all three variants, first set `OPENAI_API_KEY` locally in `.env`, then run:

```powershell
.\.venv\Scripts\python.exe eval\run.py --live-llm
```

The live command sends only the 24 held-out synthetic texts to OpenAI, makes one request per case, and reuses each response for LLM-only and hybrid scoring. This can incur provider charges. The default cost estimate uses the public `gpt-4o-mini` rates listed in [docs/RESULTS.md](./docs/RESULTS.md); for another model, pass both price-per-million options using its current rates. Each run writes its measured table to `docs/RESULTS.md`. No live LLM metrics are claimed until that command completes with a configured key.

## Privacy

- No scan on page load. The extractor is injected only after **PROTECT ME**.
- Visible text only (not CSS-hidden text, aria-labels, or alt text). This favors privacy over catching hidden content; see `docs/THREAT_MODEL.md`.
- Page text is not stored or logged by Mamoru. Matched evidence and explanations are returned to the user in the response and popup.
- After consent, only the first 12,000 characters of visible text are sent from the backend to OpenAI. The URL and title are excluded from that request. OpenAI's privacy and retention terms apply.
- API keys must stay in `.env`, never in the extension except the local shared token. `.env` and `extension/config.js` are gitignored.

## License

MIT. See `LICENSE`.
