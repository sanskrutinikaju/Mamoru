"""Compare rules-only, LLM-only, and hybrid on the fixed held-out cases."""

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import get_openai_api_key, get_openai_model
from backend.llm.provider import LLMProvider, LLMProviderError, OpenAIProvider
from backend.llm.service import LLMService
from backend.rules import RuleEngine

DATA_DIR = Path(__file__).parent / "data"
CASES_PATH = DATA_DIR / "cases.jsonl"
SPLIT_PATH = DATA_DIR / "splits.json"
RESULTS_PATH = PROJECT_ROOT / "docs" / "RESULTS.md"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_INPUT_PRICE_PER_MILLION = 0.15
DEFAULT_OUTPUT_PRICE_PER_MILLION = 0.60


@dataclass(frozen=True)
class Metrics:
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    abstentions: int
    total: int
    mean_latency_ms: float
    average_cost_usd: float | None

    @property
    def precision(self) -> float:
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else 0.0

    @property
    def false_positive_rate(self) -> float:
        denominator = self.false_positive + self.true_negative
        return self.false_positive / denominator if denominator else 0.0

    @property
    def abstain_rate(self) -> float:
        return self.abstentions / self.total if self.total else 0.0


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    """Load labeled synthetic cases without printing their text."""
    cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    required_fields = {"id", "text", "label", "category", "language"}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON in evaluation case line {line_number}.") from error

        if (
            not isinstance(case, dict)
            or set(case) != required_fields
            or not all(isinstance(value, str) and value for value in case.values())
            or case["label"] not in {"benign", "threat"}
            or case["id"] in seen_ids
        ):
            raise ValueError(f"Invalid evaluation case on line {line_number}.")
        seen_ids.add(case["id"])
        cases.append(case)

    if not cases:
        raise ValueError("The evaluation dataset contains no cases.")
    return cases


def load_split(
    cases: list[dict[str, Any]],
    split_path: Path = SPLIT_PATH,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Use a fixed held-out ID list; all other examples are training examples."""
    try:
        split_config = json.loads(split_path.read_text(encoding="utf-8"))
        held_out_ids = split_config["held_out_ids"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError("The evaluation split configuration is invalid.") from error

    if (
        not isinstance(held_out_ids, list)
        or not all(isinstance(case_id, str) for case_id in held_out_ids)
        or len(held_out_ids) != len(set(held_out_ids))
    ):
        raise ValueError("Held-out case IDs must be a unique list of strings.")

    cases_by_id = {case["id"]: case for case in cases}
    unknown_ids = set(held_out_ids) - cases_by_id.keys()
    if unknown_ids:
        raise ValueError("The split lists case IDs not found in the dataset.")

    held_out_id_set = set(held_out_ids)
    train_cases = [case for case in cases if case["id"] not in held_out_id_set]
    held_out_cases = [case for case in cases if case["id"] in held_out_id_set]
    if not train_cases or not held_out_cases:
        raise ValueError("Training and held-out splits must both contain cases.")
    return train_cases, held_out_cases


def calculate_metrics(
    cases: list[dict[str, Any]],
    predictions: list[bool],
    latencies_seconds: list[float],
    costs_usd: list[float | None] | None = None,
) -> Metrics:
    """Treat a positive finding as a threat; no finding is an abstention."""
    if not cases or len(cases) != len(predictions) or len(cases) != len(latencies_seconds):
        raise ValueError("Cases, predictions, and latencies must have matching lengths.")
    if costs_usd is not None and len(costs_usd) != len(cases):
        raise ValueError("Costs must have one value per case.")

    true_positive = false_positive = true_negative = false_negative = abstentions = 0
    for case, predicted in zip(cases, predictions):
        expected = case["label"] == "threat"
        if predicted and expected:
            true_positive += 1
        elif predicted:
            false_positive += 1
        elif expected:
            false_negative += 1
        else:
            true_negative += 1
        if not predicted:
            abstentions += 1

    known_costs = (
        [cost for cost in costs_usd if cost is not None]
        if costs_usd is not None
        else []
    )
    average_cost = sum(known_costs) / len(known_costs) if known_costs else None
    return Metrics(
        true_positive=true_positive,
        false_positive=false_positive,
        true_negative=true_negative,
        false_negative=false_negative,
        abstentions=abstentions,
        total=len(cases),
        mean_latency_ms=sum(latencies_seconds) * 1000 / len(latencies_seconds),
        average_cost_usd=average_cost,
    )


def _estimated_cost(
    prompt_tokens: int,
    completion_tokens: int,
    input_price_per_million: float,
    output_price_per_million: float,
) -> float:
    return (
        prompt_tokens * input_price_per_million
        + completion_tokens * output_price_per_million
    ) / 1_000_000


def evaluate_rules(
    cases: list[dict[str, Any]],
    engine: RuleEngine,
) -> Metrics:
    predictions: list[bool] = []
    latencies: list[float] = []
    for case in cases:
        start = time.perf_counter()
        predictions.append(bool(engine.analyze(case["text"])))
        latencies.append(time.perf_counter() - start)
    return calculate_metrics(cases, predictions, latencies, [0.0] * len(cases))


def evaluate_llm_and_hybrid(
    cases: list[dict[str, Any]],
    engine: RuleEngine,
    provider: LLMProvider,
    input_price_per_million: float,
    output_price_per_million: float,
) -> tuple[Metrics, Metrics, int]:
    """Make one LLM call per case and reuse its result for both comparisons."""
    llm_predictions: list[bool] = []
    hybrid_predictions: list[bool] = []
    llm_latencies: list[float] = []
    hybrid_latencies: list[float] = []
    llm_costs: list[float | None] = []
    failed_calls = 0
    service = LLMService(provider)

    for case in cases:
        hybrid_start = time.perf_counter()
        rule_findings = engine.analyze(case["text"])

        llm_start = time.perf_counter()
        try:
            analysis = provider.analyze(case["text"])
            llm_result = service.process_analysis(case["text"], analysis, [])
            hybrid_result = service.process_analysis(
                case["text"],
                analysis,
                rule_findings,
            )
        except LLMProviderError:
            failed_calls += 1
            llm_result = None
            hybrid_result = None
        llm_latency = time.perf_counter() - llm_start
        hybrid_latencies.append(time.perf_counter() - hybrid_start)
        llm_latencies.append(llm_latency)

        usage = provider.last_usage
        if usage is None:
            if llm_result is not None:
                raise RuntimeError(
                    "OpenAI response omitted token usage; cost cannot be measured."
                )
            llm_costs.append(None)
        else:
            llm_costs.append(
                _estimated_cost(
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    input_price_per_million,
                    output_price_per_million,
                )
            )

        llm_predictions.append(
            bool(llm_result and llm_result.findings)
        )
        hybrid_predictions.append(
            bool(rule_findings or (hybrid_result and hybrid_result.findings))
        )

    return (
        calculate_metrics(cases, llm_predictions, llm_latencies, llm_costs),
        calculate_metrics(cases, hybrid_predictions, hybrid_latencies, llm_costs),
        failed_calls,
    )


def _format_cost(cost: float | None) -> str:
    return "Not measured" if cost is None else f"${cost:.6f}"


def _format_row(name: str, metrics: Metrics | None) -> str:
    if metrics is None:
        return f"| {name} | Not run | Not run | Not run | Not run | Not run | Not run |"
    return (
        f"| {name} | {metrics.precision:.3f} | {metrics.recall:.3f} | "
        f"{metrics.false_positive_rate:.3f} | {metrics.abstain_rate:.3f} | "
        f"{metrics.mean_latency_ms:.3f} ms | {_format_cost(metrics.average_cost_usd)} |"
    )


def write_results(
    train_count: int,
    held_out_count: int,
    mode: str,
    model: str,
    input_price: float | None,
    output_price: float | None,
    rules_metrics: Metrics,
    llm_metrics: Metrics | None,
    hybrid_metrics: Metrics | None,
    failed_calls: int,
) -> None:
    """Write the reproducible run's table, without claiming missing results."""
    price_note = (
        f"Input: ${input_price:g}/1M tokens; output: ${output_price:g}/1M tokens."
        if input_price is not None and output_price is not None
        else "LLM pricing was not used in this run."
    )
    content = f"""# Mamoru Evaluation Results

Last run: {date.today().isoformat()}  
Mode: {mode}  
Dataset: {train_count + held_out_count} synthetic cases; fixed held-out split of {held_out_count}; {train_count} training cases are not used in these metrics.  
LLM model: {model if llm_metrics is not None else "not run"}  
Token pricing used: {price_note}

| Variant | Precision | Recall | False-positive rate | Abstain rate | Mean latency | Estimated cost per scan (USD) |
|---|---:|---:|---:|---:|---:|---:|
{_format_row("Rules only", rules_metrics)}
{_format_row("LLM only", llm_metrics)}
{_format_row("Hybrid", hybrid_metrics)}

Failed or invalid LLM calls: {failed_calls if llm_metrics is not None else "not run"} of {held_out_count if llm_metrics is not None else "not run"}.

## How to interpret this table

- The held-out IDs are fixed in `eval/data/splits.json`. Rule and prompt tuning must use training cases only. The evaluator sends only held-out text to the provider.
- The default live-run prices for `gpt-4o-mini` are $0.15 per million input tokens and $0.60 per million output tokens, based on the [OpenAI API pricing page](https://openai.com/api/pricing/). Verify current rates before a live run; both values can be overridden on the command line.
- A positive prediction means at least one finding was returned. No finding is counted as an abstention and as a negative prediction for precision, recall, and false-positive-rate calculations.
- Latency is measured once per held-out case on this machine and includes any provider retries. It is not a benchmark.
- LLM and hybrid costs use provider-reported prompt/completion tokens and the listed input/output rates. The average includes only successful calls with reported usage; failed calls are excluded. They are estimates: account-specific discounts, cached-input pricing, taxes, and failed-request billing can differ.
- Rules-only cost is $0. LLM-only and hybrid share one provider call per case; hybrid does not double the API usage.
- These results use small, synthetic, English-only cases. They are not a held-out real-world security evaluation and do not establish production performance.
- If LLM metrics say `Not run`, no LLM performance or cost claim is made. Configure `OPENAI_API_KEY` locally, then run `eval/run.py --live-llm` to measure the provider variants.
"""
    RESULTS_PATH.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--rules-only", action="store_true", help="Run offline held-out rules metrics.")
    mode.add_argument(
        "--live-llm",
        action="store_true",
        help="Send held-out synthetic text to OpenAI and compare all three variants.",
    )
    parser.add_argument("--input-price-per-million", type=float)
    parser.add_argument("--output-price-per-million", type=float)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = load_cases()
    train_cases, held_out_cases = load_split(cases)
    engine = RuleEngine()
    rules_metrics = evaluate_rules(held_out_cases, engine)
    llm_metrics = hybrid_metrics = None
    failed_calls = 0
    model = DEFAULT_MODEL
    input_price = output_price = None

    if args.live_llm:
        if not get_openai_api_key():
            raise SystemExit(
                "OPENAI_API_KEY is not configured. Add it locally to .env; "
                "do not paste it into chat or commit it."
            )
        model = get_openai_model()
        if model == DEFAULT_MODEL:
            input_price = (
                DEFAULT_INPUT_PRICE_PER_MILLION
                if args.input_price_per_million is None
                else args.input_price_per_million
            )
            output_price = (
                DEFAULT_OUTPUT_PRICE_PER_MILLION
                if args.output_price_per_million is None
                else args.output_price_per_million
            )
        elif (
            args.input_price_per_million is not None
            and args.output_price_per_million is not None
        ):
            input_price = args.input_price_per_million
            output_price = args.output_price_per_million
        else:
            raise SystemExit(
                "For a non-default model, pass both --input-price-per-million "
                "and --output-price-per-million using current provider pricing."
            )
        if input_price < 0 or output_price < 0:
            raise SystemExit("Token prices must not be negative.")

        provider = OpenAIProvider(
            api_key=get_openai_api_key(),
            model=model,
        )
        llm_metrics, hybrid_metrics, failed_calls = evaluate_llm_and_hybrid(
            held_out_cases,
            engine,
            provider,
            input_price,
            output_price,
        )

    run_mode = "rules-only" if args.rules_only else "live LLM comparison"
    write_results(
        train_count=len(train_cases),
        held_out_count=len(held_out_cases),
        mode=run_mode,
        model=model,
        input_price=input_price,
        output_price=output_price,
        rules_metrics=rules_metrics,
        llm_metrics=llm_metrics,
        hybrid_metrics=hybrid_metrics,
        failed_calls=failed_calls,
    )
    print(f"Cases: {len(cases)} ({len(train_cases)} training; {len(held_out_cases)} held out)")
    print(f"Mode: {run_mode}")
    print("| Variant | Precision | Recall | FPR | Abstain | Mean latency | Cost/scan |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    print(_format_row("Rules only", rules_metrics))
    print(_format_row("LLM only", llm_metrics))
    print(_format_row("Hybrid", hybrid_metrics))
    if llm_metrics is not None:
        print(f"LLM calls with failure/invalid output: {failed_calls}")
    print(f"Results written to {RESULTS_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
