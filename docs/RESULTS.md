# Mamoru Evaluation Results

Last run: 2026-11-05

Mode: rules-only baseline plus partial live Gemini attempt (paused at 13/48)

Dataset: 144 explicitly synthetic cases; 96 training; 48 fixed held-out.

Held-out groups: core 24; hand-written scam-style 24.

LLM provider/model: Google Gemini Developer API / gemini-3.5-flash-lite (partial live results only)

No real webpage text or user scans are in this evaluation dataset. The hand-written group was authored for this project and uses fictional `.test` domains.

## Partial live evaluation (13/48 held-out cases)

The live batch stopped on the free-tier rate limit after 13 of 48 held-out cases had cached outcomes: 12 valid Gemini results and 1 provider failure. Thirty-five cases remain unevaluated. All 13 are explicitly synthetic and belong to the core group; no scam-style cases were reached. The cache is resumable at `eval/.cache/gemini-37a58c167b3b.json`. These partial results are not full-cohort estimates.

| Variant | Provider / model | Cases | TP | FP | TN | FN | Precision (raw / %) | Recall (raw / %) | FPR (raw / %) | Abstain rate (raw / %) | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rules only | Mamoru rules | 13 | 0 | 3 | 9 | 1 | 0/3 (0.0%) | 0/1 (0.0%) | 3/12 (25.0%) | 10/13 (76.9%) | 0.01 ms |
| Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 13 | 1 | 1 | 11 | 0 | 1/2 (50.0%) | 1/1 (100.0%) | 1/12 (8.3%) | 11/13 (84.6%) | 2558.81 ms |
| Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 13 | 1 | 3 | 9 | 0 | 1/4 (25.0%) | 1/1 (100.0%) | 3/12 (25.0%) | 9/13 (69.2%) | 2558.82 ms |

### Partial results by category

| Group | Category | Variant | Provider / model | Cases | TP | FP | TN | FN | Recall (raw / %) | FPR (raw / %) | Abstain rate (raw / %) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| core | credential_request | Rules only | Mamoru rules | 1 | 0 | 0 | 0 | 1 | 0/1 (0.0%) | n/a | 1/1 (100.0%) |
| core | credential_request | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 1 | 1 | 0 | 0 | 0 | 1/1 (100.0%) | n/a | 0/1 (0.0%) |
| core | credential_request | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 1 | 1 | 0 | 0 | 0 | 1/1 (100.0%) | n/a | 0/1 (0.0%) |
| core | none | Rules only | Mamoru rules | 12 | 0 | 3 | 9 | 0 | n/a | 3/12 (25.0%) | 9/12 (75.0%) |
| core | none | Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 12 | 0 | 1 | 11 | 0 | n/a | 1/12 (8.3%) | 11/12 (91.7%) |
| core | none | Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 12 | 0 | 3 | 9 | 0 | n/a | 3/12 (25.0%) | 9/12 (75.0%) |

### Partial High versus Medium correctness

| Variant | Provider / model | High correct (raw / %) | Medium correct (raw / %) | Comparison |
|---|---|---:|---:|---|
| Rules only | Mamoru rules | 0/2 (0.0%) | 0/1 (0.0%) | Equal correctness |
| Gemini only | Google Gemini Developer API / gemini-3.5-flash-lite | 1/1 (100.0%) | n/a | Insufficient cases at one or both levels |
| Hybrid | Mamoru rules + Google Gemini Developer API / gemini-3.5-flash-lite | 1/3 (33.3%) | 0/1 (0.0%) | High more often correct |

For this partial 13-case subset only, Hybrid (F1 0.400) is below the best single variant, Gemini only (F1 0.667). This is not a full-cohort comparison.

## Dataset provenance and evaluation-history limitations

- The dataset marks all 24 scam-style cases **AI-written** and none **human-written**. The authoring-session transcript is unavailable in this checkout, so the recorded attribution could not be independently audited here.
- The original 24 core held-out IDs remain held out. The 24 AI-written scam-style cases were added to the held-out group; none of the original held-out cases moved into training.
- No deterministic rules were changed after the first held-out rules results were shown. The system prompt wording was kept, but the provider-specific request envelope and structured-output schema were adapted from OpenAI Chat Completions to Gemini GenerateContent. Therefore comparisons to earlier OpenAI-era measurements are not like-for-like; the first results must not be used as if they were Gemini results.
- The intended live report uses 48 held-out cases. Only 13 core cases have live outcomes so far, so there is no complete live comparison with the first 24-case results.

## Full-cohort rules-only baseline (48 held-out cases)

The Gemini-only and Hybrid entries in this baseline table were not run in that rules-only run. The separate partial live results above are limited to 13 cases.

| Variant | Provider / model | Cases | TP | FP | TN | FN | Precision (raw / %) | Recall (raw / %) | FPR (raw / %) | Abstain rate (raw / %) | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rules only | Mamoru rules | 48 | 6 | 4 | 12 | 26 | 6/10 (60.0%) | 6/32 (18.8%) | 4/16 (25.0%) | 38/48 (79.2%) | 0.01 ms |
| Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | Not run | Not run | Not run | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | Not run | Not run | Not run | Not run | Not run | Not run | Not run | Not run | Not run | Not run |

## Results by dataset group and category

| Group | Labeled category | Variant | Provider / model | Cases | TP | FP | TN | FN | Recall (raw / %) | FPR (raw / %) | Abstain rate (raw / %) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| core | credential_request | Rules only | Mamoru rules | 3 | 0 | 0 | 0 | 3 | 0/3 (0.0%) | n/a | 3/3 (100.0%) |
| core | credential_request | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | credential_request | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | deceptive_link | Rules only | Mamoru rules | 3 | 0 | 0 | 0 | 3 | 0/3 (0.0%) | n/a | 3/3 (100.0%) |
| core | deceptive_link | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | deceptive_link | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | none | Rules only | Mamoru rules | 12 | 0 | 3 | 9 | 0 | n/a | 3/12 (25.0%) | 9/12 (75.0%) |
| core | none | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 12 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | none | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 12 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | prompt_injection | Rules only | Mamoru rules | 3 | 0 | 0 | 0 | 3 | 0/3 (0.0%) | n/a | 3/3 (100.0%) |
| core | prompt_injection | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | prompt_injection | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | urgency_pressure | Rules only | Mamoru rules | 3 | 1 | 0 | 0 | 2 | 1/3 (33.3%) | n/a | 2/3 (66.7%) |
| core | urgency_pressure | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| core | urgency_pressure | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | credential_request | Rules only | Mamoru rules | 5 | 1 | 0 | 0 | 4 | 1/5 (20.0%) | n/a | 4/5 (80.0%) |
| handwritten_scam_style | credential_request | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 5 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | credential_request | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 5 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | deceptive_link | Rules only | Mamoru rules | 5 | 0 | 0 | 0 | 5 | 0/5 (0.0%) | n/a | 5/5 (100.0%) |
| handwritten_scam_style | deceptive_link | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 5 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | deceptive_link | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 5 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | none | Rules only | Mamoru rules | 4 | 0 | 1 | 3 | 0 | n/a | 1/4 (25.0%) | 3/4 (75.0%) |
| handwritten_scam_style | none | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 4 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | none | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 4 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | prompt_injection | Rules only | Mamoru rules | 5 | 2 | 0 | 0 | 3 | 2/5 (40.0%) | n/a | 3/5 (60.0%) |
| handwritten_scam_style | prompt_injection | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 5 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | prompt_injection | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 5 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | urgency_pressure | Rules only | Mamoru rules | 5 | 2 | 0 | 0 | 3 | 2/5 (40.0%) | n/a | 3/5 (60.0%) |
| handwritten_scam_style | urgency_pressure | Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | 5 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| handwritten_scam_style | urgency_pressure | Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | 5 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |

## Calibration check: High versus Medium

Correctness here means the case label is `threat`; this is not probability calibration. Each cell reports correct cases / all cases at that report level.

| Variant | Provider / model | High correct (raw / %) | Medium correct (raw / %) | Comparison |
|---|---|---:|---:|---|
| Rules only | Mamoru rules | 3/5 (60.0%) | 3/5 (60.0%) | Equal correctness |
| Gemini only | Google Gemini Developer API / not run (GEMINI_MODEL required) | Not run | Not run | Not run |
| Hybrid | Mamoru rules + Google Gemini Developer API / not run (GEMINI_MODEL required) | Not run | Not run | Not run |

## Gemini usage and reliability

- Google Gemini Developer API / gemini-3.5-flash-lite: input 2,925, output 290, thinking 0, total 3,215 tokens across 12/13 cached outcomes with usage metadata.
- Google Gemini Developer API / gemini-3.5-flash-lite: invalid outputs 0/13; provider failures 1/13; rate-limit responses 2; recorded API attempts 18.
- The cache at `eval/.cache/gemini-37a58c167b3b.json` contains the 13 processed outcomes and is retained for resuming.
- Request timeout: 15 seconds. Transient network/server errors receive at most one retry. Calls use `GEMINI_MIN_SECONDS_BETWEEN_CALLS` (default 12 seconds) and `GEMINI_MAX_CALLS_PER_RUN` (default 40 outbound attempts). A 429 stops immediately with completed/remaining counts; cached outcomes are reused on rerun.
- The cached provider failure has no stored HTTP status or error message. Its cause is unknown, and the failed entry is reused rather than retried on resume.
- Billing cost is not estimated: free-tier eligibility and account billing status cannot be verified by this script. Verify the active project and tier in Google AI Studio before running. A billing-enabled project may incur charges.

## Interpretation and limitations

- The fixed held-out IDs are in `eval/data/splits.json`; the evaluator never uses them to tune rules or prompts.
- A positive prediction means at least one finding was returned. No finding is counted as an abstention and as a negative prediction. Confusion counts and percentages use only the held-out cases.
- The hand-written scam-style group is reported separately from the core examples. It contains synthetic examples, not copied messages or real brands.
- Latencies are measured on this machine and are not benchmarks. Cached Gemini calls retain the original measured latency and token usage.
- Gemini free-tier inputs and outputs may be used by Google to improve its products and may be reviewed by humans. Only synthetic cases are sent. See the [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms).
- The full 48-case Gemini and Hybrid variants did not complete. The partial-subset comparison above is not a full-cohort conclusion.
- These results are from synthetic text only; they do not establish production or real-world detection performance.
- Reproduce offline metrics with `python eval/run.py --rules-only`; reproduce the live comparison with `python eval/run.py --live-gemini` after configuring `GEMINI_API_KEY` locally and verifying the free tier.
