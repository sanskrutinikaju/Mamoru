# Mamoru Evaluation Results

Last run: 2026-11-07

Mode: live Gemini comparison

Dataset: 144 explicitly synthetic cases; 96 training; 48 fixed held-out.

Held-out groups: core 24; hand-written scam-style 24.

LLM provider/model: Google Gemini Developer API / gemini-3.5-flash-lite

No real webpage text or user scans are in this evaluation dataset. The hand-written group was authored for this project and uses fictional `.test` domains.

## Dataset provenance and evaluation-history limitations

- The dataset marks all 24 scam-style cases **AI-written** and none **human-written**. The authoring-session transcript is unavailable in this checkout, so the recorded attribution could not be independently audited here.
- The original 24 core held-out IDs remain held out. The 24 AI-written scam-style cases were added to the held-out group; none of the original held-out cases moved into training.
- No deterministic rules were changed after the first held-out rules results were shown. The system prompt wording was kept, but the provider-specific request envelope and structured-output schema were adapted from OpenAI Chat Completions to Gemini GenerateContent. Therefore comparisons to earlier OpenAI-era measurements are not like-for-like; the first results must not be used as if they were Gemini results.
- The live report uses 48 held-out cases, so the first 24-case metrics and current 48-case metrics have different sample composition.

## Aggregate held-out results

| Variant | Provider / model | Cases | TP | FP | TN | FN | Precision (raw / %) | Recall (raw / %) | FPR (raw / %) | Abstain rate (raw / %) | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rules only | Mamoru rules | 48 | 6 | 4 | 12 | 26 | 6/10 (60.0%) | 6/32 (18.8%) | 4/16 (25.0%) | 38/48 (79.2%) | 0.02 ms |
| Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 48 | 32 | 2 | 14 | 0 | 32/34 (94.1%) | 32/32 (100.0%) | 2/16 (12.5%) | 14/48 (29.2%) | 10689.47 ms |
| Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 48 | 32 | 5 | 11 | 0 | 32/37 (86.5%) | 32/32 (100.0%) | 5/16 (31.2%) | 11/48 (22.9%) | 10689.50 ms |

## Results by dataset group and category

| Group | Labeled category | Variant | Provider / model | Cases | TP | FP | TN | FN | Recall (raw / %) | FPR (raw / %) | Abstain rate (raw / %) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| core | credential_request | Rules only | Mamoru rules | 3 | 0 | 0 | 0 | 3 | 0/3 (0.0%) | n/a | 3/3 (100.0%) |
| core | credential_request | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 3 | 3 | 0 | 0 | 0 | 3/3 (100.0%) | n/a | 0/3 (0.0%) |
| core | credential_request | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 3 | 3 | 0 | 0 | 0 | 3/3 (100.0%) | n/a | 0/3 (0.0%) |
| core | deceptive_link | Rules only | Mamoru rules | 3 | 0 | 0 | 0 | 3 | 0/3 (0.0%) | n/a | 3/3 (100.0%) |
| core | deceptive_link | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 3 | 3 | 0 | 0 | 0 | 3/3 (100.0%) | n/a | 0/3 (0.0%) |
| core | deceptive_link | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 3 | 3 | 0 | 0 | 0 | 3/3 (100.0%) | n/a | 0/3 (0.0%) |
| core | none | Rules only | Mamoru rules | 12 | 0 | 3 | 9 | 0 | n/a | 3/12 (25.0%) | 9/12 (75.0%) |
| core | none | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 12 | 0 | 1 | 11 | 0 | n/a | 1/12 (8.3%) | 11/12 (91.7%) |
| core | none | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 12 | 0 | 3 | 9 | 0 | n/a | 3/12 (25.0%) | 9/12 (75.0%) |
| core | prompt_injection | Rules only | Mamoru rules | 3 | 0 | 0 | 0 | 3 | 0/3 (0.0%) | n/a | 3/3 (100.0%) |
| core | prompt_injection | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 3 | 3 | 0 | 0 | 0 | 3/3 (100.0%) | n/a | 0/3 (0.0%) |
| core | prompt_injection | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 3 | 3 | 0 | 0 | 0 | 3/3 (100.0%) | n/a | 0/3 (0.0%) |
| core | urgency_pressure | Rules only | Mamoru rules | 3 | 1 | 0 | 0 | 2 | 1/3 (33.3%) | n/a | 2/3 (66.7%) |
| core | urgency_pressure | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 3 | 3 | 0 | 0 | 0 | 3/3 (100.0%) | n/a | 0/3 (0.0%) |
| core | urgency_pressure | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 3 | 3 | 0 | 0 | 0 | 3/3 (100.0%) | n/a | 0/3 (0.0%) |
| handwritten_scam_style | credential_request | Rules only | Mamoru rules | 5 | 1 | 0 | 0 | 4 | 1/5 (20.0%) | n/a | 4/5 (80.0%) |
| handwritten_scam_style | credential_request | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 5 | 5 | 0 | 0 | 0 | 5/5 (100.0%) | n/a | 0/5 (0.0%) |
| handwritten_scam_style | credential_request | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 5 | 5 | 0 | 0 | 0 | 5/5 (100.0%) | n/a | 0/5 (0.0%) |
| handwritten_scam_style | deceptive_link | Rules only | Mamoru rules | 5 | 0 | 0 | 0 | 5 | 0/5 (0.0%) | n/a | 5/5 (100.0%) |
| handwritten_scam_style | deceptive_link | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 5 | 5 | 0 | 0 | 0 | 5/5 (100.0%) | n/a | 0/5 (0.0%) |
| handwritten_scam_style | deceptive_link | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 5 | 5 | 0 | 0 | 0 | 5/5 (100.0%) | n/a | 0/5 (0.0%) |
| handwritten_scam_style | none | Rules only | Mamoru rules | 4 | 0 | 1 | 3 | 0 | n/a | 1/4 (25.0%) | 3/4 (75.0%) |
| handwritten_scam_style | none | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 4 | 0 | 1 | 3 | 0 | n/a | 1/4 (25.0%) | 3/4 (75.0%) |
| handwritten_scam_style | none | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 4 | 0 | 2 | 2 | 0 | n/a | 2/4 (50.0%) | 2/4 (50.0%) |
| handwritten_scam_style | prompt_injection | Rules only | Mamoru rules | 5 | 2 | 0 | 0 | 3 | 2/5 (40.0%) | n/a | 3/5 (60.0%) |
| handwritten_scam_style | prompt_injection | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 5 | 5 | 0 | 0 | 0 | 5/5 (100.0%) | n/a | 0/5 (0.0%) |
| handwritten_scam_style | prompt_injection | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 5 | 5 | 0 | 0 | 0 | 5/5 (100.0%) | n/a | 0/5 (0.0%) |
| handwritten_scam_style | urgency_pressure | Rules only | Mamoru rules | 5 | 2 | 0 | 0 | 3 | 2/5 (40.0%) | n/a | 3/5 (60.0%) |
| handwritten_scam_style | urgency_pressure | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 5 | 5 | 0 | 0 | 0 | 5/5 (100.0%) | n/a | 0/5 (0.0%) |
| handwritten_scam_style | urgency_pressure | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 5 | 5 | 0 | 0 | 0 | 5/5 (100.0%) | n/a | 0/5 (0.0%) |

## Calibration check: High versus Medium

Correctness here means the case label is `threat`; this is not probability calibration. Each cell reports correct cases / all cases at that report level.

| Variant | Provider / model | High correct (raw / %) | Medium correct (raw / %) | Comparison |
|---|---|---:|---:|---|
| Rules only | Mamoru rules | 3/5 (60.0%) | 3/5 (60.0%) | Equal correctness |
| Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 21/21 (100.0%) | 11/11 (100.0%) | Equal correctness |
| Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 21/23 (91.3%) | 11/13 (84.6%) | High more often correct |

## Gemini usage and reliability

- Google Gemini Developer API / gemini-3.5-flash-lite: input 12,004, output 3,719, thinking 0, total 15,723 tokens across 48/48 calls with usage metadata.
- Google Gemini Developer API / gemini-3.5-flash-lite: invalid outputs 0/48; provider failures 0/48; rate-limit responses 2; cache hits 45; new API attempts 58.
- Cache hits: 45; cache misses: 3; API attempts: 58; rate-limit responses: 2. Results contain only synthetic case IDs, synthetic-derived findings, token counts, and timings.
- Failed cases retried: 2; retries that succeeded: 2; retries that failed again: 0.
- Request timeout: 15 seconds. Transient network/server errors receive at most one retry. Request spacing and the per-run HTTP call cap are configurable with `GEMINI_MIN_SECONDS_BETWEEN_CALLS` (default 12) and `GEMINI_MAX_CALLS_PER_RUN` (default 40). A 429 stops immediately with completed/remaining counts; cached outcomes are reused on rerun.
- Billing cost is not estimated: free-tier eligibility and account billing status cannot be verified by this script. Verify the active project and tier in Google AI Studio before running. A billing-enabled project may incur charges.

## Interpretation and limitations

- The fixed held-out IDs are in `eval/data/splits.json`; the evaluator never uses them to tune rules or prompts.
- A positive prediction means at least one finding was returned. No finding is counted as an abstention and as a negative prediction. Confusion counts and percentages use only the held-out cases.
- The hand-written scam-style group is reported separately from the core examples. It contains synthetic examples, not copied messages or real brands.
- Latencies are measured on this machine and are not benchmarks. Cached Gemini calls retain the original measured latency and token usage.
- Gemini free-tier inputs and outputs may be used by Google to improve its products and may be reviewed by humans. Only synthetic cases are sent. See the [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms).
- Hybrid is not better than the best single variant on F1 (0.928 vs 0.970).
- These results are from synthetic text only; they do not establish production or real-world detection performance.
- Reproduce offline metrics with `python eval/run.py --rules-only`; reproduce the live comparison with `python eval/run.py --live-gemini` after configuring `GEMINI_API_KEY` locally and verifying the free tier.
