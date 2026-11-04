import json
from pathlib import Path

import pytest

from backend.llm.provider import LLMProviderError, TokenUsage
from backend.rules import RuleEngine
from eval.run import (
    calculate_metrics,
    evaluate_llm_and_hybrid,
    load_cases,
    load_split,
)
from backend.schemas.analysis import LLMAnalysis

PROJECT_ROOT = Path(__file__).parents[1]
CASES_PATH = PROJECT_ROOT / "eval" / "data" / "cases.jsonl"
SPLIT_PATH = PROJECT_ROOT / "eval" / "data" / "splits.json"


def test_synthetic_dataset_has_120_unique_labeled_cases_and_fixed_split():
    cases = load_cases(CASES_PATH)
    train_cases, held_out_cases = load_split(cases, SPLIT_PATH)

    assert len(cases) == 120
    assert len({case["id"] for case in cases}) == 120
    assert len(train_cases) == 96
    assert len(held_out_cases) == 24
    assert sum(case["label"] == "benign" for case in held_out_cases) == 12
    assert sum(case["label"] == "threat" for case in held_out_cases) == 12


def test_split_rejects_unknown_held_out_ids(tmp_path):
    split_path = tmp_path / "splits.json"
    split_path.write_text(
        json.dumps({"held_out_ids": ["unknown-case"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not found"):
        load_split(load_cases(CASES_PATH), split_path)


def test_metrics_treat_no_finding_as_abstention_and_negative_prediction():
    cases = [
        {"label": "threat"},
        {"label": "threat"},
        {"label": "benign"},
        {"label": "benign"},
    ]

    result = calculate_metrics(
        cases,
        [True, False, True, False],
        [0.001, 0.002, 0.003, 0.004],
        [0.1, 0.2, 0.3, 0.4],
    )

    assert result.true_positive == 1
    assert result.false_positive == 1
    assert result.true_negative == 1
    assert result.false_negative == 1
    assert result.precision == 0.5
    assert result.recall == 0.5
    assert result.false_positive_rate == 0.5
    assert result.abstain_rate == 0.5
    assert result.mean_latency_ms == pytest.approx(2.5)
    assert result.average_cost_usd == pytest.approx(0.25)


def test_live_comparison_reuses_one_provider_call_per_case():
    class FakeProvider:
        last_usage = TokenUsage(prompt_tokens=100, completion_tokens=10)

        def __init__(self):
            self.calls = 0

        def analyze(self, page_text):
            del page_text
            self.calls += 1
            self.last_usage = TokenUsage(prompt_tokens=100, completion_tokens=10)
            return LLMAnalysis(findings=[])

    _, held_out_cases = load_split(load_cases(CASES_PATH), SPLIT_PATH)
    provider = FakeProvider()
    llm_metrics, hybrid_metrics, failed_calls = evaluate_llm_and_hybrid(
        held_out_cases,
        RuleEngine(),
        provider,
        input_price_per_million=0.15,
        output_price_per_million=0.60,
    )

    assert provider.calls == len(held_out_cases)
    assert failed_calls == 0
    assert llm_metrics.total == len(held_out_cases)
    assert llm_metrics.abstentions == len(held_out_cases)
    assert llm_metrics.average_cost_usd == pytest.approx(0.000021)
    assert hybrid_metrics.recall >= llm_metrics.recall


def test_live_comparison_counts_provider_failures_without_guessing_cost():
    class FailedProvider:
        last_usage = None

        def analyze(self, page_text):
            del page_text
            raise LLMProviderError("Synthetic provider failure.")

    _, held_out_cases = load_split(load_cases(CASES_PATH), SPLIT_PATH)
    llm_metrics, _, failed_calls = evaluate_llm_and_hybrid(
        held_out_cases,
        RuleEngine(),
        FailedProvider(),
        input_price_per_million=0.15,
        output_price_per_million=0.60,
    )

    assert failed_calls == len(held_out_cases)
    assert llm_metrics.average_cost_usd is None
