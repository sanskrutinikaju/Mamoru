# Mamoru Safety Report

The Safety Report summarizes text signals returned by Mamoru's deterministic
rules. The report schema can combine model findings for evaluation, but live
page scans use local rules only. Mamoru never sends live page text to Gemini.
The report is a review aid, not proof that a page is harmful or safe.

## Overall levels

The report uses the strongest severity among its findings:

| Level | Meaning |
|---|---|
| **High** | At least one finding has High severity. Review its evidence carefully. |
| **Medium** | No High finding exists, and at least one finding has Medium severity. Review before proceeding. |
| **Low** | Findings exist, and all are Low severity. This is not a safety guarantee. |
| **Cannot tell** | No findings were returned. Mamoru cannot infer that the page is safe. |

These are deliberately simple rules, not statistically learned thresholds.
Deterministic rule severities are configured in `backend/rules/rules.json`.
LLM severities use the same three labels and cannot lower the severity of a
matching deterministic category. The highest finding therefore sets the report
level. An empty result is **Cannot tell**, rather than Low, because a lack of
matches does not establish safety.

## Finding confidence

Confidence is a qualitative description of agreement between Mamoru's sources,
not a probability or calibrated score:

- **High**: a deterministic rule and the LLM returned the same category and
  exact evidence span.
- **Medium**: a deterministic rule found the span but the LLM did not return
  the same category and span.
- **Low**: the finding came from the LLM only.

These labels do not measure whether the page is actually malicious. A rule can
match quoted or educational text, and a model can misinterpret context. Current
live scans use rules only, so their rule findings have Medium confidence. Gemini
is used only with synthetic evaluation cases. The user should review the
evidence and explanation.

## Synthetic level check

`eval/run.py` runs deterministic rules only and compares the accuracy of High
and Medium overall levels on the synthetic labeled examples. Accuracy here
means the fraction of cases at that
level whose label is `threat`. Cases labeled `benign` count as incorrect
positive risk reports. `Cannot tell` and Low reports are excluded from this
comparison. The script also says whether High was correct more often than
Medium on that dataset.

This is a small sanity check, not statistical calibration, a held-out test, or
a claim about real websites. The current case set is hand-written and too
small to establish reliable real-world performance. Report only numbers
reproduced by the script, and do not tune rules against a future held-out set.
