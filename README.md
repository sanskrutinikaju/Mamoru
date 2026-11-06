# Mamoru（マモル）

Mamoru is a consent-first browser threat analyzer. It stays inactive until you click **PROTECT ME**, preview the extracted text, and confirm. Then the extension sends that text to a **local** Python API on your computer.

This is an engineering portfolio project. It is not a finished security product.

## Current status 

**Phase 5 — Live evaluation** is in progress:

- User click → visible text preview → confirm → `POST /analyze`
- Shared secret token + CORS limited to the configured extension origin
- Character and request-body size limits, plus validation that does not echo page text
- Deterministic rules return severity, category, description, and matched text evidence
- Gemini is reserved for synthetic evaluation cases; real webpage text stays on-device
- A Safety Report summarizes severity, evidence, explanation, confidence, and a **Cannot tell** outcome
- The extension displays the report as plain text; findings are signals, not proof
- Live scans explicitly state that Gemini is disabled for real page text
- A 144-case synthetic dataset has a fixed 48-case held-out split, including a separate 24-case hand-written scam-style group
- The evaluator compares rules-only, Gemini-only, and hybrid results without tuning on held-out examples

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

Set `GEMINI_API_KEY` and a currently available exact `GEMINI_MODEL` ID in `.env` for live evaluation of the synthetic test cases. There is deliberately no built-in model default: the evaluator stops with a clear error if the model ID is missing or malformed, and reports a model/request error if Google does not recognize it. The key stays on your computer and is used only by the evaluation script. The backend never sends live webpage text to Gemini; it uses deterministic rules for scans.

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

After setting the extension origin and token, restart the backend. Then open a normal webpage → click Mamoru → **PROTECT ME** → review the displayed preview and data-sharing notice → **Proceed**. The preview shows only the first 300 characters; proceeding sends the full extracted visible text to the local backend. Real page text remains on your computer and is never sent to Gemini.

The backend runs deterministic text rules. It does not send scan text to any language-model provider. The Gemini evaluator sends only the synthetic examples stored in `eval/data/` after you run it. Rules are limited signals, not a complete threat detector or proof of harm.

The Safety Report uses the strongest finding severity; when no finding is returned it says **Cannot tell**, not Low or safe. Confidence labels describe agreement between rule and model sources, not a probability; current live scans use rules only, and real page text is never sent to Gemini. See [SAFETY_REPORT.md](<C:/Users/sanskruti  Nikaju/Documents/Mamoru/docs/SAFETY_REPORT.md>) for meanings and thresholds.

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

To compare all three variants, first configure `GEMINI_API_KEY` in `.env`, verify that the Gemini API project is on the free tier, and then run:

```powershell
.\.venv\Scripts\python.exe eval\run.py --live-gemini
```

The live command sends only the fixed held-out synthetic texts to Gemini and reuses each response for Gemini-only and hybrid scoring. The dataset marks all 24 scam-style cases AI-written and none human-written; their original authoring transcript is not available in this checkout for independent verification. Results are cached in ignored `eval/.cache/` files; cached outcomes are reused on a rerun, including after a rate limit. A cached provider failure is also reused and is not automatically retried. Set `GEMINI_MIN_SECONDS_BETWEEN_CALLS` to control the minimum gap between outbound requests (default `12` seconds), and `GEMINI_MAX_CALLS_PER_RUN` to cap outbound HTTP attempts per evaluator process, including transient retries (default `40`). A 429 stops immediately with completed and remaining case counts; completed outcomes remain cached. Provider errors report the HTTP status, Google's status string, and a message truncated to 300 characters after removing API-key and request-content matches. Gemini free-tier inputs and outputs may be used by Google to improve its products and may be reviewed by humans. Never put real webpage text, personal information, or confidential material in the evaluation dataset. The evaluator writes measured results to `docs/RESULTS.md`; it does not claim unmeasured LLM results. Check the [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms) and [current pricing and tier](https://ai.google.dev/gemini-api/docs/pricing) before running. A billing-enabled project may incur charges; the code cannot determine or guarantee your account's tier.

## Privacy

- No scan on page load. The extractor is injected only after **PROTECT ME**.
- Visible text only (not CSS-hidden text, aria-labels, or alt text). This favors privacy over catching hidden content; see `docs/THREAT_MODEL.md`.
- Page text is not stored or logged by Mamoru. Matched evidence and explanations are returned to the user in the response and popup.
- Real scan text is sent only to the local backend and is never sent to Gemini. Only synthetic cases from `eval/data/` are sent by the evaluation script.
- Gemini free-tier evaluation prompts and responses may be used by Google to improve its products and may be reviewed by humans; see the linked provider terms before evaluation.
- API keys must stay in `.env`, never in the extension except the local shared token. `.env` and `extension/config.js` are gitignored.

## License

MIT. See `LICENSE`.
