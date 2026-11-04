# Mamoru threat model (Phase 1)

This is a simple description of what Mamoru tries to protect, who might attack it, and what it does **not** do yet. It is not a guarantee of safety.

## What we are trying to protect

- The **user’s decision** to share page text: nothing is sent until they click **PROTECT ME** and then **Proceed**.
- **Secrets on the backend**, such as a future LLM API key. Those stay in `.env` on the user’s machine, never in the extension.
- The **local API** so a random website cannot easily use Mamoru as a hidden service.

Webpage text is **untrusted data**. Mamoru must never treat that text as instructions.

## Who the attackers are

1. **A malicious webpage**  
   Tries to phish, harvest passwords, hide a bad link, or include text like “ignore your instructions” aimed at an AI.

2. **A webpage that calls the local API**  
   JavaScript on a site could try `fetch("http://127.0.0.1:8000/analyze", ...)`.  
   **Defense now:** the browser’s CORS check only allows `chrome-extension://` pages, and `/analyze` requires a shared secret header. Other **local programs** (PowerShell, another app) can still call localhost if they know or guess the token.

3. **A prompt-injecting page**  
   The page text tries to control a future LLM. **Not defended in software yet** (no LLM in this phase). The design rule is: page text is data, not commands.

4. **Another process on the same computer**  
   Can often reach `127.0.0.1`. If they can read your project folder, they can read `.env` and `extension/config.js`. Mamoru does **not** defend against a fully compromised PC.

## What we defend against (Phase 1)

- Automatic scanning (we do not scan until the user clicks).
- A normal website reading the JSON response from our API (CORS).
- A normal website sending a JSON `/analyze` request without the token (preflight + 401).
- Accidentally logging or echoing page text in API errors.
- Oversized dumps of text (size limit).

## What we do not defend against (non-goals)

- Malware already on the user’s computer.
- Phishing that never appears in **visible** text (see extraction tradeoff below).
- Detecting phishing or injection (no rule engine or LLM in this phase).
- HTTPS for the local API (it is localhost only).
- Hiding the token from someone who has the extension files.

## Extraction tradeoff: visible text vs hidden text

**Current choice: visible text only** (what you would roughly see on the page). We do **not** collect CSS-hidden text, `aria-label`, or image `alt` as extra channels.

| Choice | Better for | Worse for |
|---|---|---|
| Visible only (now) | Privacy: less extra page data | Hidden attacks in `display:none`, labels, or alt text may be missed |
| Also hidden / aria / alt | Catching hidden prompt injection or extra lure text | More collection; more chance of grabbing UI chrome the user did not mean to send |

We can switch later if evaluation shows hidden text is needed. Changing it is a product decision, not a silent default.

## Honest limits

Phase 1 only **hardens the pipe**. It does not decide if a page is a scam.
