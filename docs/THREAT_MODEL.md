# Mamoru threat model (current implementation)

This is a simple description of what Mamoru tries to protect, who might attack it, and what it does **not** do yet. It is not a guarantee of safety.

## What we are trying to protect

- The **user’s decision** to share page text: nothing is sent until they click **PROTECT ME** and then **Proceed**.
- **Secrets on the backend**, such as the OpenAI API key. They stay in `.env` on the user’s machine, never in the extension.
- The **local API** so a random website cannot easily use Mamoru as a hidden service.

Webpage text is **untrusted data**. Mamoru must never treat that text as instructions.

## Who the attackers are

1. **A malicious webpage**  
   Tries to phish, harvest passwords, hide a bad link, or include text like “ignore your instructions” aimed at an AI.

2. **A webpage that calls the local API**  
   JavaScript on a site could try `fetch("http://127.0.0.1:8000/analyze", ...)`.  
   **Defense now:** browser CORS allows only the exact extension origin configured in `MAMORU_EXTENSION_ORIGIN`, and `/analyze` requires a shared token header. Other **local programs** can still call localhost; the token is not protection against someone who can read the extension files or run code as your user.

3. **A prompt-injecting page**  
   The page text tries to control the LLM. The backend sends it as JSON-encoded, explicitly delimited untrusted data and instructs the model not to follow it. This reduces risk but cannot guarantee the model will always ignore malicious instructions.

4. **Another process on the same computer**  
   Can often reach `127.0.0.1`. If they can read your project folder, they can read `.env` and `extension/config.js`. Mamoru does **not** defend against a fully compromised PC.

## What we defend against (implemented protections)

- Automatic scanning (we do not scan until the user clicks).
- A normal website reading the JSON response from our API (CORS).
- A normal website using Mamoru's browser API origin (exact-origin CORS check).
- Requests to `/analyze` without the shared token (401).
- Accidentally logging or echoing page text in API errors.
- Oversized request bodies, including streamed bodies without a `Content-Length` header.
- A small set of deterministic text patterns for credential requests, urgency pressure, prompt-injection phrases, and suspicious link wording.

## What we do not defend against (non-goals)

- Malware already on the user’s computer.
- Phishing that never appears in **visible** text (see extraction tradeoff below).
- Proving a page is safe or detecting every phishing or injection attempt; rules may miss or incorrectly flag text.
- Comparing a link's displayed label to its actual destination; the backend receives visible text only.
- Prompt injection succeeding despite the model's untrusted-data instructions and delimiters.
- HTTPS for the local API (it is localhost only).
- Hiding the token from someone who has the extension files.

## Extraction choice: visible text only

Mamoru collects visible page text only (what a person can roughly see). It does **not** collect CSS-hidden text, accessibility labels such as `aria-label`, or image descriptions such as `alt`.

| Choice | Better for | Worse for |
|---|---|---|
| Visible only (current) | Privacy: less extra page data is shared | Hidden attacks in `display:none`, labels, or image descriptions may be missed |
| Also hidden / labels / image descriptions | Could reveal additional hidden instructions or lures | Collects more page data and may include interface text the user did not intend to share |

We chose visible-only extraction for Phase 1. Changing this later requires an explicit product decision and a clear preview of the additional data.

## Local API limits

- The backend accepts browser requests only from the exact extension origin set in `.env`; an empty setting allows no browser origin.
- `/analyze` requires the shared token. Because the extension needs that token to make requests, it is visible to someone who can read the local extension files. This is not a defense against other programs running as the same user.
- Request bodies have a byte limit even when sent as a stream without a declared `Content-Length`; the text field also has its own character limit.
- Logs include request method, path, and response status only. Validation errors are generic and do not echo submitted text.
- Matched evidence is included in the response for the user to review; it is not logged or stored.

## Rule results

Rules look for a small number of text patterns. A match is a signal to review, not proof that a page is malicious. The API returns at most one matching text span per rule, and the extension displays those spans as plain text. No match is not a safety guarantee.

## Safety Report

The overall level is the strongest severity among the findings. With no
findings, the result is **Cannot tell**; it never means the page is safe.
Finding confidence is qualitative: High means a rule and the LLM agree on the
category and exact evidence, Medium means a rule-only match, and Low means an
LLM-only finding. These labels are not probabilities. See
`docs/SAFETY_REPORT.md` for the threshold definitions and the limits of the
synthetic calibration check.

## LLM data flow and limits

- The user must confirm before the local backend receives extracted page text.
- If `OPENAI_API_KEY` is configured, Mamoru sends only the first 12,000 characters of visible page text to the single OpenAI provider. The URL, page title, consent timestamp, and word count are not included in that provider request.
- The extension's confirmation screen states this external transfer before the user proceeds. OpenAI's privacy and retention terms apply to any text it receives; users should review the provider terms for their account before enabling the key.
- The API key remains on the backend in `.env`; it is not sent to the extension.
- Provider calls have a 15-second timeout and at most one retry. Invalid output, a timeout, network failure, provider error, or missing key leaves deterministic findings available and reports an explicit LLM status.
- LLM output is validated against a strict Pydantic schema. Evidence must exactly occur in the minimized input, and a deterministic rule's severity is a floor that the LLM cannot lower.
- Mamoru does not store or log page text. Text is sent to OpenAI only after consent and is subject to the provider's data-handling terms.

## Honest limits

Mamoru's rules and LLM can miss or incorrectly flag page content. They do not prove that a page is safe or harmful.
