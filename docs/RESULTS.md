# Mamoru Evaluation Results

Last run: 2026-11-04  
Mode: rules-only  
Dataset: 120 synthetic cases; fixed held-out split of 24; 96 training cases are not used in these metrics.  
LLM model: not run  
Token pricing used: LLM pricing was not used in this run.

| Variant | Precision | Recall | False-positive rate | Abstain rate | Mean latency | Estimated cost per scan (USD) |
|---|---:|---:|---:|---:|---:|---:|
| Rules only | 0.250 | 0.083 | 0.250 | 0.833 | 0.009 ms | $0.000000 |
| LLM only | Not run | Not run | Not run | Not run | Not run | Not run |
| Hybrid | Not run | Not run | Not run | Not run | Not run | Not run |

Failed or invalid LLM calls: not run of not run.

## How to interpret this table

- The held-out IDs are fixed in `eval/data/splits.json`. Rule and prompt tuning must use training cases only. The evaluator sends only held-out text to the provider.
- The default live-run prices for `gpt-4o-mini` are $0.15 per million input tokens and $0.60 per million output tokens, based on the [OpenAI API pricing page](https://openai.com/api/pricing/). Verify current rates before a live run; both values can be overridden on the command line.
- A positive prediction means at least one finding was returned. No finding is counted as an abstention and as a negative prediction for precision, recall, and false-positive-rate calculations.
- Latency is measured once per held-out case on this machine and includes any provider retries. It is not a benchmark.
- LLM and hybrid costs use provider-reported prompt/completion tokens and the listed input/output rates. The average includes only successful calls with reported usage; failed calls are excluded. They are estimates: account-specific discounts, cached-input pricing, taxes, and failed-request billing can differ.
- Rules-only cost is $0. LLM-only and hybrid share one provider call per case; hybrid does not double the API usage.
- These results use small, synthetic, English-only cases. They are not a held-out real-world security evaluation and do not establish production performance.
- If LLM metrics say `Not run`, no LLM performance or cost claim is made. Configure `OPENAI_API_KEY` locally, then run `eval/run.py --live-llm` to measure the provider variants.
