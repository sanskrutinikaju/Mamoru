"""Evaluate rules-only, Gemini-only, and hybrid on synthetic held-out cases."""

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import (  # noqa: E402
    get_gemini_api_key,
    get_gemini_max_calls_per_run,
    get_gemini_min_seconds_between_calls,
    get_gemini_model,
)
from backend.llm.provider import (  # noqa: E402
    LLMCallLimitError,
    LLMInvalidResponseError,
    LLMProviderError,
    LLMRateLimitError,
    LLMProvider,
    SYSTEM_PROMPT,
    TokenUsage,
    GeminiProvider,
)
from backend.llm.service import LLMService  # noqa: E402
from backend.reporting import build_safety_report  # noqa: E402
from backend.rules import RuleEngine  # noqa: E402
from backend.schemas.analysis import LLMAnalysis  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
CASES_PATH = DATA_DIR / "cases.jsonl"
SPLIT_PATH = DATA_DIR / "splits.json"
CACHE_DIR = Path(__file__).parent / ".cache"
RESULTS_PATH = PROJECT_ROOT / "docs" / "RESULTS.md"
CASE_FIELDS = {
    "id",
    "text",
    "label",
    "category",
    "language",
    "synthetic",
    "group",
}
OPTIONAL_CASE_FIELDS = {"authorship"}
CASE_GROUPS = {"core", "handwritten_scam_style"}
CASE_CATEGORIES = {
    "none",
    "credential_request",
    "urgency_pressure",
    "prompt_injection",
    "deceptive_link",
}
CACHE_FORMAT_VERSION = 2
PROVIDER_NAME = "Google Gemini Developer API"

ProviderStatus = Literal["completed", "invalid", "failed"]


@dataclass(frozen=True)
class CaseMetrics:
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    abstentions: int
    total: int
    mean_latency_ms: float

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

    @property
    def f1(self) -> float:
        denominator = self.precision + self.recall
        return (
            2 * self.precision * self.recall / denominator
            if denominator
            else 0.0
        )


@dataclass(frozen=True)
class VariantResult:
    prediction: bool
    report_level: str
    latency_seconds: float
    status: ProviderStatus | Literal["not_run", "rules"]
    token_usage: TokenUsage | None = None
    attempts: int = 0


@dataclass(frozen=True)
class LiveResults:
    llm: list[VariantResult]
    hybrid: list[VariantResult]
    cache_hits: int
    cache_misses: int
    api_attempts: int
    rate_limit_responses: int


class EvaluationPaused(Exception):
    """The live batch stopped at a rate limit or configured call cap."""

    def __init__(self, completed: int, total: int, reason: str) -> None:
        self.completed = completed
        self.total = total
        self.remaining = total - completed
        super().__init__(
            f"Gemini evaluation stopped ({reason}): {completed} cases completed; "
            f"{self.remaining} remain. Completed synthetic results are cached."
        )


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    """Load cases explicitly marked synthetic; never echo their text on errors."""
    cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON in evaluation case line {line_number}.") from error

        if (
            not isinstance(case, dict)
            or not CASE_FIELDS.issubset(case)
            or set(case) - CASE_FIELDS - OPTIONAL_CASE_FIELDS
            or not isinstance(case.get("id"), str)
            or not case["id"]
            or not isinstance(case.get("text"), str)
            or not case["text"]
            or case.get("label") not in {"benign", "threat"}
            or case.get("category") not in CASE_CATEGORIES
            or not isinstance(case.get("language"), str)
            or not case["language"]
            or case.get("synthetic") is not True
            or case.get("group") not in CASE_GROUPS
            or case["id"] in seen_ids
        ):
            raise ValueError(f"Invalid or non-synthetic evaluation case on line {line_number}.")

        if case["group"] == "handwritten_scam_style" and not case["id"].startswith(
            "handwritten-scam-"
        ):
            raise ValueError(f"Invalid AI-written scam-style case ID on line {line_number}.")
        if case["group"] == "handwritten_scam_style" and case.get("authorship") != "AI-written":
            raise ValueError(
                f"AI-written scam-style cases must declare AI-written authorship on line {line_number}."
            )
        if case["group"] == "core" and case["id"].startswith("handwritten-scam-"):
            raise ValueError(f"Invalid core case ID on line {line_number}.")

        seen_ids.add(case["id"])
        cases.append(case)

    if not cases:
        raise ValueError("The evaluation dataset contains no cases.")
    if not any(case["group"] == "handwritten_scam_style" for case in cases):
        raise ValueError("The AI-written scam-style group is missing.")
    return cases


def load_split(
    cases: list[dict[str, Any]],
    split_path: Path = SPLIT_PATH,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Use a fixed held-out ID list; all other synthetic examples are training."""
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
    if any(case["synthetic"] is not True for case in held_out_cases):
        raise ValueError("Every held-out case must be explicitly marked synthetic.")
    return train_cases, held_out_cases


def calculate_metrics(
    cases: list[dict[str, Any]],
    predictions: list[bool],
    latencies_seconds: list[float],
) -> CaseMetrics:
    """Treat no finding as an abstention and as a negative prediction."""
    if (
        not cases
        or len(cases) != len(predictions)
        or len(cases) != len(latencies_seconds)
    ):
        raise ValueError("Cases, predictions, and latencies must have matching lengths.")

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

    return CaseMetrics(
        true_positive=true_positive,
        false_positive=false_positive,
        true_negative=true_negative,
        false_negative=false_negative,
        abstentions=abstentions,
        total=len(cases),
        mean_latency_ms=sum(latencies_seconds) * 1000 / len(latencies_seconds),
    )


def evaluate_rules(
    cases: list[dict[str, Any]],
    engine: RuleEngine,
) -> list[VariantResult]:
    results: list[VariantResult] = []
    for case in cases:
        started = time.perf_counter()
        findings = engine.analyze(case["text"])
        elapsed = time.perf_counter() - started
        report = build_safety_report(findings, [])
        results.append(
            VariantResult(
                prediction=bool(findings),
                report_level=report.overallLevel,
                latency_seconds=elapsed,
                status="rules",
            )
        )
    return results


def _case_digest(case: dict[str, Any], model: str) -> str:
    text_digest = hashlib.sha256(case["text"].encode("utf-8")).hexdigest()
    material = "\n".join((model, case["id"], text_digest, SYSTEM_PROMPT))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class EvaluationCache:
    """Persist only model results for the explicitly synthetic evaluation set."""

    def __init__(
        self,
        path: Path,
        model: str,
        allowed_cases: list[dict[str, Any]],
    ) -> None:
        if any(case.get("synthetic") is not True for case in allowed_cases):
            raise ValueError("The evaluation cache accepts only synthetic cases.")
        self.path = path
        self.model = model
        self.allowed_inputs = {
            case["id"]: hashlib.sha256(case["text"].encode("utf-8")).hexdigest()
            for case in allowed_cases
        }
        self.allowed_texts = {case["id"]: case["text"] for case in allowed_cases}
        self.entries: dict[str, dict[str, Any]] = {}
        self.rate_limit_events: dict[str, int] = {}
        self.rate_limit_attempts: dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            cache = json.loads(self.path.read_text(encoding="utf-8"))
            if (
                not isinstance(cache, dict)
                or cache.get("format_version") != CACHE_FORMAT_VERSION
                or cache.get("model") != self.model
                or not isinstance(cache.get("entries"), dict)
            ):
                raise ValueError
            rate_limit_events = cache.get("rate_limit_events", {})
            rate_limit_attempts = cache.get("rate_limit_attempts", {})
            if not isinstance(rate_limit_events, dict) or not isinstance(
                rate_limit_attempts, dict
            ):
                raise ValueError
            for counts in (rate_limit_events, rate_limit_attempts):
                for case_id, count in counts.items():
                    if (
                        case_id not in self.allowed_inputs
                        or not isinstance(count, int)
                        or isinstance(count, bool)
                        or count < 1
                    ):
                        raise ValueError
            if rate_limit_events.keys() != rate_limit_attempts.keys():
                raise ValueError
            for case_id in rate_limit_events:
                if rate_limit_attempts[case_id] < rate_limit_events[case_id]:
                    raise ValueError
            for digest, entry in cache["entries"].items():
                self._validate_entry(digest, entry)
            self.entries = cache["entries"]
            self.rate_limit_events = rate_limit_events
            self.rate_limit_attempts = rate_limit_attempts
        except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError):
            raise ValueError(
                "The ignored Gemini evaluation cache is invalid. Remove that "
                "specific cache file and rerun the synthetic evaluation."
            ) from None

    def _validate_entry(self, digest: str, entry: object) -> None:
        fields = {
            "case_id",
            "input_sha256",
            "model",
            "status",
            "findings",
            "latency_seconds",
            "prompt_tokens",
            "completion_tokens",
            "thoughts_tokens",
            "attempts",
        }
        if (
            not isinstance(digest, str)
            or not isinstance(entry, dict)
            or not fields.issubset(entry)
            or set(entry) - fields - {"previous_failures"}
            or entry.get("model") != self.model
            or entry.get("case_id") not in self.allowed_inputs
            or entry.get("input_sha256")
            != self.allowed_inputs.get(entry.get("case_id"))
            or entry.get("status") not in {"completed", "invalid", "failed"}
            or not isinstance(entry.get("findings"), list)
            or not isinstance(entry.get("latency_seconds"), (int, float))
            or isinstance(entry.get("latency_seconds"), bool)
            or not math.isfinite(entry["latency_seconds"])
            or entry["latency_seconds"] < 0
            or not isinstance(entry.get("attempts"), int)
            or isinstance(entry.get("attempts"), bool)
            or entry["attempts"] < 1
        ):
            raise ValueError
        previous_failures = entry.get("previous_failures", [])
        if not isinstance(previous_failures, list):
            raise ValueError
        for previous in previous_failures:
            if (
                not isinstance(previous, dict)
                or previous.get("status") != "failed"
                or "previous_failures" in previous
            ):
                raise ValueError
            self._validate_entry(digest, previous)
        for token_field in ("prompt_tokens", "completion_tokens", "thoughts_tokens"):
            value = entry.get(token_field)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise ValueError
        if entry["status"] == "completed":
            analysis = LLMAnalysis.model_validate({"findings": entry["findings"]})
            if any(
                finding.evidence not in self.allowed_texts[entry["case_id"]]
                for finding in analysis.findings
            ):
                raise ValueError
        elif entry["findings"]:
            raise ValueError
        if digest != self._entry_key(entry):
            raise ValueError

    def _entry_key(self, entry: dict[str, Any]) -> str:
        return hashlib.sha256(
            "\n".join(
                (
                    self.model,
                    entry["case_id"],
                    entry["input_sha256"],
                    SYSTEM_PROMPT,
                )
            ).encode("utf-8")
        ).hexdigest()

    def get(self, case: dict[str, Any]) -> dict[str, Any] | None:
        if case.get("synthetic") is not True:
            raise ValueError("Gemini evaluation is restricted to synthetic cases.")
        digest = _case_digest(case, self.model)
        entry = self.entries.get(digest)
        return entry

    def put(self, case: dict[str, Any], entry: dict[str, Any]) -> None:
        if case.get("synthetic") is not True:
            raise ValueError("Gemini evaluation is restricted to synthetic cases.")
        digest = _case_digest(case, self.model)
        self._validate_entry(digest, entry)
        self.entries[digest] = entry
        self._save()

    def record_rate_limit(self, case: dict[str, Any], attempts: int) -> None:
        if (
            case.get("synthetic") is not True
            or case["id"] not in self.allowed_inputs
            or hashlib.sha256(case["text"].encode("utf-8")).hexdigest()
            != self.allowed_inputs[case["id"]]
        ):
            raise ValueError("Rate-limit cache accepts only known synthetic cases.")
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
            raise ValueError("Rate-limit attempts must be a positive integer.")
        case_id = case["id"]
        self.rate_limit_events[case_id] = self.rate_limit_events.get(case_id, 0) + 1
        self.rate_limit_attempts[case_id] = (
            self.rate_limit_attempts.get(case_id, 0) + attempts
        )
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(
            {
                "format_version": CACHE_FORMAT_VERSION,
                "model": self.model,
                "entries": self.entries,
                "rate_limit_events": self.rate_limit_events,
                "rate_limit_attempts": self.rate_limit_attempts,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self.path.parent,
                delete=False,
            ) as temporary:
                temporary_path = temporary.name
                temporary.write(content)
                temporary.write("\n")
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path is not None and os.path.exists(temporary_path):
                os.unlink(temporary_path)

    @property
    def total_api_attempts(self) -> int:
        completed_attempts = sum(
            entry["attempts"] for entry in self.entries.values()
        )
        rate_limited_attempts = sum(self.rate_limit_attempts.values())
        return completed_attempts + rate_limited_attempts


def _token_usage_from_entry(entry: dict[str, Any]) -> TokenUsage | None:
    prompt = entry["prompt_tokens"]
    completion = entry["completion_tokens"]
    thoughts = entry["thoughts_tokens"]
    if prompt is None or completion is None:
        return None
    return TokenUsage(prompt, completion, thoughts or 0)


def _cache_entry(
    case: dict[str, Any],
    model: str,
    status: ProviderStatus,
    analysis: LLMAnalysis,
    latency_seconds: float,
    usage: TokenUsage | None,
    attempts: int,
) -> dict[str, Any]:
    return {
        "case_id": case["id"],
        "input_sha256": hashlib.sha256(case["text"].encode("utf-8")).hexdigest(),
        "model": model,
        "status": status,
        "findings": (
            [finding.model_dump(mode="json") for finding in analysis.findings]
            if status == "completed"
            else []
        ),
        "latency_seconds": latency_seconds,
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "thoughts_tokens": usage.thoughts_tokens if usage else None,
        "attempts": attempts,
    }


def evaluate_gemini(
    cases: list[dict[str, Any]],
    engine: RuleEngine,
    provider: LLMProvider,
    cache: EvaluationCache,
    retry_failed: bool = True,
) -> LiveResults:
    """Use one cached Gemini result per case for LLM-only and hybrid scoring."""
    if any(case.get("synthetic") is not True for case in cases):
        raise ValueError("Only explicitly synthetic cases may be sent to Gemini.")

    llm_results: list[VariantResult] = []
    hybrid_results: list[VariantResult] = []
    cache_hits = cache_misses = processed = 0
    service = LLMService(provider)

    for case in cases:
        rules_started = time.perf_counter()
        rule_findings = engine.analyze(case["text"])
        rule_latency = time.perf_counter() - rules_started

        entry = cache.get(case)
        previous_failure = (
            entry if retry_failed and entry and entry["status"] == "failed" else None
        )
        if entry is None or previous_failure is not None:
            cache_misses += 1
            request_started = time.perf_counter()
            try:
                analysis = provider.analyze(case["text"])
                service_result = service.process_analysis(case["text"], analysis, [])
                if service_result.status != "completed":
                    raise LLMInvalidResponseError(
                        "Gemini analysis did not complete validation."
                    )
                status: ProviderStatus = "completed"
            except LLMRateLimitError:
                cache.record_rate_limit(case, provider.last_attempt_count)
                raise EvaluationPaused(
                    processed, len(cases), "rate limit"
                ) from None
            except LLMCallLimitError:
                raise EvaluationPaused(
                    processed, len(cases), "per-run call cap"
                ) from None
            except LLMInvalidResponseError:
                status = "invalid"
                analysis = LLMAnalysis(findings=[])
            except LLMProviderError:
                status = "failed"
                analysis = LLMAnalysis(findings=[])

            elapsed = time.perf_counter() - request_started
            usage = provider.last_usage
            attempts = provider.last_attempt_count
            entry = _cache_entry(
                case,
                cache.model,
                status,
                analysis,
                elapsed,
                usage,
                attempts,
            )
            if previous_failure is not None:
                entry["previous_failures"] = [
                    *previous_failure.get("previous_failures", []),
                    {
                        key: value
                        for key, value in previous_failure.items()
                        if key != "previous_failures"
                    },
                ]
            cache.put(case, entry)
        else:
            cache_hits += 1

        status = entry["status"]
        usage = _token_usage_from_entry(entry)
        llm_findings = LLMAnalysis.model_validate(
            {"findings": entry["findings"]}
        ).findings

        if status != "completed":
            llm_findings = []
        llm_report = build_safety_report([], llm_findings)
        hybrid_report = build_safety_report(rule_findings, llm_findings)
        elapsed = float(entry["latency_seconds"])
        attempts = entry["attempts"]
        llm_results.append(
            VariantResult(
                prediction=bool(llm_findings),
                report_level=llm_report.overallLevel,
                latency_seconds=elapsed,
                status=status,
                token_usage=usage,
                attempts=attempts,
            )
        )
        hybrid_results.append(
            VariantResult(
                prediction=bool(rule_findings or llm_findings),
                report_level=hybrid_report.overallLevel,
                latency_seconds=elapsed + rule_latency,
                status=status,
                token_usage=usage,
                attempts=attempts,
            )
        )
        processed += 1

    return LiveResults(
        llm=llm_results,
        hybrid=hybrid_results,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        api_attempts=cache.total_api_attempts,
        rate_limit_responses=sum(cache.rate_limit_events.values()),
    )


def _percentage(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator}/{denominator} ({numerator / denominator:.1%})"


def _variant_metrics(
    cases: list[dict[str, Any]],
    results: list[VariantResult] | None,
) -> CaseMetrics | None:
    if results is None:
        return None
    return calculate_metrics(
        cases,
        [result.prediction for result in results],
        [result.latency_seconds for result in results],
    )


def _format_variant_row(
    name: str,
    provider_label: str,
    cases: list[dict[str, Any]],
    results: list[VariantResult] | None,
) -> str:
    metrics = _variant_metrics(cases, results)
    if metrics is None:
        return (
            f"| {name} | {provider_label} | Not run | Not run | Not run | "
            "Not run | Not run | Not run | Not run | Not run | Not run | Not run |"
        )
    return (
        f"| {name} | {provider_label} | {metrics.total} | "
        f"{metrics.true_positive} | {metrics.false_positive} | "
        f"{metrics.true_negative} | {metrics.false_negative} | "
        f"{_percentage(metrics.true_positive, metrics.true_positive + metrics.false_positive)} | "
        f"{_percentage(metrics.true_positive, metrics.true_positive + metrics.false_negative)} | "
        f"{_percentage(metrics.false_positive, metrics.false_positive + metrics.true_negative)} | "
        f"{_percentage(metrics.abstentions, metrics.total)} | "
        f"{metrics.mean_latency_ms:.2f} ms |"
    )


def _variant_records(
    live: LiveResults | None,
    rules: list[VariantResult],
    model: str | None,
) -> list[tuple[str, str, list[VariantResult] | None]]:
    if live is None:
        not_run_label = f"{PROVIDER_NAME} / not run (GEMINI_MODEL required)"
        return [
            ("Rules only", "Mamoru rules", rules),
            ("Gemini only", not_run_label, None),
            ("Hybrid", f"Mamoru rules + {not_run_label}", None),
        ]
    return [
        ("Rules only", "Mamoru rules", rules),
        ("Gemini only", f"{PROVIDER_NAME} / {model}", live.llm),
        ("Hybrid", f"Mamoru rules + {PROVIDER_NAME} / {model}", live.hybrid),
    ]


def _calibration_row(
    name: str,
    provider_label: str,
    cases: list[dict[str, Any]],
    results: list[VariantResult] | None,
) -> str:
    if results is None:
        return f"| {name} | {provider_label} | Not run | Not run | Not run |"
    high_total = high_correct = medium_total = medium_correct = 0
    for case, result in zip(cases, results):
        actual_threat = case["label"] == "threat"
        if result.report_level == "High":
            high_total += 1
            high_correct += int(actual_threat)
        elif result.report_level == "Medium":
            medium_total += 1
            medium_correct += int(actual_threat)

    if not high_total or not medium_total:
        comparison = "Insufficient cases at one or both levels"
    elif high_correct / high_total > medium_correct / medium_total:
        comparison = "High more often correct"
    elif high_correct / high_total < medium_correct / medium_total:
        comparison = "Medium more often correct"
    else:
        comparison = "Equal correctness"
    return (
        f"| {name} | {provider_label} | "
        f"{_percentage(high_correct, high_total)} | "
        f"{_percentage(medium_correct, medium_total)} | {comparison} |"
    )


def _token_summary(results: list[VariantResult] | None, model: str | None) -> str:
    label = f"{PROVIDER_NAME} / {model}" if model else "Gemini not run"
    if results is None:
        return f"- {label}: not run."
    usages = [result.token_usage for result in results if result.token_usage is not None]
    if not usages:
        return f"- {label}: token usage not returned for any case."
    prompt = sum(usage.prompt_tokens for usage in usages)
    completion = sum(usage.completion_tokens for usage in usages)
    thoughts = sum(usage.thoughts_tokens for usage in usages)
    known_calls = len(usages)
    return (
        f"- {label}: input {prompt:,}, output {completion:,}, "
        f"thinking {thoughts:,}, total {prompt + completion + thoughts:,} tokens "
        f"across {known_calls}/{len(results)} calls with usage metadata."
    )


def _provider_quality(
    live: LiveResults | None,
    model: str | None,
    case_count: int,
) -> str:
    if live is None:
        return "- Gemini invalid outputs: not run. Gemini provider failures: not run."
    results = live.llm
    invalid = sum(result.status == "invalid" for result in results)
    failed = sum(result.status == "failed" for result in results)
    return (
        f"- {PROVIDER_NAME} / {model}: invalid outputs {invalid}/{case_count}; "
        f"provider failures {failed}/{case_count}; rate-limit responses "
        f"{live.rate_limit_responses}; cache hits {live.cache_hits}; "
        f"new API attempts {live.api_attempts}."
    )


def _category_rows(
    cases: list[dict[str, Any]],
    results: list[tuple[str, str, list[VariantResult] | None]],
) -> list[str]:
    rows: list[str] = []
    for group in ("core", "handwritten_scam_style"):
        group_label = (
            "AI-written scam-style" if group == "handwritten_scam_style" else group
        )
        for category in sorted(CASE_CATEGORIES):
            selected = [
                index
                for index, case in enumerate(cases)
                if case["group"] == group and case["category"] == category
            ]
            if not selected:
                continue
            selected_cases = [cases[index] for index in selected]
            for name, provider_label, variant_results in results:
                selected_results = (
                    [variant_results[index] for index in selected]
                    if variant_results is not None
                    else None
                )
                metrics = _variant_metrics(selected_cases, selected_results)
                if metrics is None:
                    rows.append(
                        f"| {group_label} | {category} | {name} | {provider_label} | "
                        f"{len(selected_cases)} | Not run | Not run | Not run | Not run | "
                        "Not run | Not run | Not run |"
                    )
                    continue
                rows.append(
                    f"| {group_label} | {category} | {name} | {provider_label} | "
                    f"{metrics.total} | {metrics.true_positive} | {metrics.false_positive} | "
                    f"{metrics.true_negative} | {metrics.false_negative} | "
                    f"{_percentage(metrics.true_positive, metrics.true_positive + metrics.false_negative)} | "
                    f"{_percentage(metrics.false_positive, metrics.false_positive + metrics.true_negative)} | "
                    f"{_percentage(metrics.abstentions, metrics.total)} |"
                )
    return rows


def write_results(
    train_cases: list[dict[str, Any]],
    held_out_cases: list[dict[str, Any]],
    rules: list[VariantResult],
    live: LiveResults | None,
    model: str | None,
    cache: EvaluationCache | None = None,
) -> None:
    """Write all numbers from this evaluator run, labeling every model result."""
    variants = _variant_records(live, rules, model)
    group_counts = {
        group: sum(case["group"] == group for case in held_out_cases)
        for group in ("core", "handwritten_scam_style")
    }
    aggregate_rows = "\n".join(
        _format_variant_row(name, provider_label, held_out_cases, results)
        for name, provider_label, results in variants
    )
    category_rows = "\n".join(_category_rows(held_out_cases, variants))
    calibration_rows = "\n".join(
        _calibration_row(name, provider_label, held_out_cases, results)
        for name, provider_label, results in variants
    )
    llm_results = live.llm if live is not None else None
    total_cases = len(held_out_cases)
    hybrid_metrics = _variant_metrics(
        held_out_cases,
        live.hybrid if live is not None else None,
    )
    single_metrics = [
        metrics
        for metrics in (
            _variant_metrics(held_out_cases, rules),
            _variant_metrics(held_out_cases, llm_results),
        )
        if metrics is not None
    ]
    comparison = (
        "Live variants were not run, so no hybrid-versus-single comparison is available."
    )
    if hybrid_metrics is not None and llm_results is not None:
        best_single_f1 = max(metrics.f1 for metrics in single_metrics)
        if hybrid_metrics.f1 > best_single_f1:
            comparison = (
                f"Hybrid is better than the best single variant on F1 "
                f"({hybrid_metrics.f1:.3f} vs {best_single_f1:.3f})."
            )
        else:
            comparison = (
                f"Hybrid is not better than the best single variant on F1 "
                f"({hybrid_metrics.f1:.3f} vs {best_single_f1:.3f})."
            )
    llm_provider_model = (
        f"{PROVIDER_NAME} / {model}"
        if model and live is not None
        else f"{PROVIDER_NAME} / not run; configure GEMINI_MODEL"
    )
    retry_entries = [
        entry
        for entry in (cache.entries.values() if cache is not None else [])
        if entry.get("previous_failures")
    ]
    failed_cases_retried = sum(
        len(entry["previous_failures"]) for entry in retry_entries
    )
    retries_succeeded = sum(entry["status"] == "completed" for entry in retry_entries)
    retries_failed_again = sum(
        max(0, len(entry["previous_failures"]) - 1)
        + (entry["status"] == "failed")
        for entry in retry_entries
    )
    cache_line = (
        f"- Cache hits: {live.cache_hits}; cache misses: {live.cache_misses}; "
        f"API attempts: {live.api_attempts}; rate-limit responses: "
        f"{live.rate_limit_responses}. Results contain only synthetic case IDs, "
        "synthetic-derived findings, token counts, and timings."
        if live is not None
        else "- Gemini cache was not used in this rules-only run."
    )
    retry_line = (
        f"- Failed cases retried: {failed_cases_retried}; retries that succeeded: "
        f"{retries_succeeded}; retries that failed again: {retries_failed_again}."
    )

    content = f"""# Mamoru Evaluation Results

Last run: {date.today().isoformat()}

Mode: {"rules-only" if live is None else "live Gemini comparison"}

Dataset: {len(train_cases) + len(held_out_cases)} explicitly synthetic cases; {len(train_cases)} training; {total_cases} fixed held-out.

Held-out groups: core {group_counts["core"]}; AI-written scam-style {group_counts["handwritten_scam_style"]}.

LLM provider/model: {llm_provider_model}

No real webpage text or user scans are in this evaluation dataset. Dataset metadata labels the scam-style examples AI-written; they use fictional `.test` domains.

## Dataset provenance and evaluation-history limitations

- Dataset metadata labels all 24 scam-style cases **AI-written**.
- The original 24 core held-out IDs remain held out. The 24 AI-written scam-style cases were added to the held-out group; none of the original held-out cases moved into training.
- No deterministic rules were changed after the first held-out rules results were shown. The system prompt wording was kept, but the provider-specific request envelope and structured-output schema were adapted from OpenAI Chat Completions to Gemini GenerateContent. Therefore comparisons to earlier OpenAI-era measurements are not like-for-like; the first results must not be used as if they were Gemini results.
- The live report uses 48 held-out cases, so the first 24-case metrics and current 48-case metrics have different sample composition.

## Aggregate held-out results

| Variant | Provider / model | Cases | TP | FP | TN | FN | Precision (raw / %) | Recall (raw / %) | FPR (raw / %) | Abstain rate (raw / %) | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{aggregate_rows}

## Results by dataset group and category

| Group | Labeled category | Variant | Provider / model | Cases | TP | FP | TN | FN | Recall (raw / %) | FPR (raw / %) | Abstain rate (raw / %) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
{category_rows}

## Calibration check: High versus Medium

Correctness here means the case label is `threat`; this is not probability calibration. Each cell reports correct cases / all cases at that report level.

| Variant | Provider / model | High correct (raw / %) | Medium correct (raw / %) | Comparison |
|---|---|---:|---:|---|
{calibration_rows}

## Gemini usage and reliability

{_token_summary(llm_results, model)}
{_provider_quality(live, model, total_cases)}
{cache_line}
{retry_line}
- Request timeout: 15 seconds. Transient network/server errors receive at most one retry. Request spacing and the per-run HTTP call cap are configurable with `GEMINI_MIN_SECONDS_BETWEEN_CALLS` (default 12) and `GEMINI_MAX_CALLS_PER_RUN` (default 40). A 429 stops immediately with completed/remaining counts; cached outcomes are reused on rerun.
- Billing cost is not estimated: free-tier eligibility and account billing status cannot be verified by this script. Verify the active project and tier in Google AI Studio before running. A billing-enabled project may incur charges.

## Interpretation and limitations

- The fixed held-out IDs are in `eval/data/splits.json`; the evaluator never uses them to tune rules or prompts.
- A positive prediction means at least one finding was returned. No finding is counted as an abstention and as a negative prediction. Confusion counts and percentages use only the held-out cases.
- The AI-written scam-style group is reported separately from the core examples. It contains synthetic examples, not copied messages or real brands.
- Near-perfect Gemini scores on AI-written synthetic data likely reflect easy, stylistically recognizable cases and should not be generalized beyond this dataset. Here, "abstain" means no findings were returned; it is not a "cannot tell" outcome.
- Latencies are measured on this machine and are not benchmarks. Cached Gemini calls retain the original measured latency and token usage.
- Gemini free-tier inputs and outputs may be used by Google to improve its products and may be reviewed by humans. Only synthetic cases are sent. See the [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms).
- {comparison}
- These results are from synthetic text only; they do not establish production or real-world detection performance.
- Reproduce offline metrics with `python eval/run.py --rules-only`; reproduce the live comparison with `python eval/run.py --live-gemini` after configuring `GEMINI_API_KEY` locally and verifying the free tier.
"""
    RESULTS_PATH.write_text(content, encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--rules-only", action="store_true", help="Run the offline rules evaluation.")
    mode.add_argument(
        "--live-gemini",
        action="store_true",
        help="Send held-out synthetic cases to Gemini for the three-way comparison.",
    )
    parser.add_argument(
        "--no-retry-failed",
        action="store_true",
        help="Reuse cached failed Gemini results without retrying them.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    cases = load_cases()
    train_cases, held_out_cases = load_split(cases)
    engine = RuleEngine()
    rules = evaluate_rules(held_out_cases, engine)
    live = None
    model = None
    cache = None

    if args.live_gemini:
        api_key = get_gemini_api_key()
        if not api_key:
            raise SystemExit(
                "GEMINI_API_KEY is not configured. Add it locally to .env; "
                "do not paste it into chat or commit it."
            )
        try:
            model = get_gemini_model()
        except ValueError as error:
            raise SystemExit(str(error)) from None
        try:
            min_seconds_between_calls = get_gemini_min_seconds_between_calls()
            max_calls_per_run = get_gemini_max_calls_per_run()
        except ValueError as error:
            raise SystemExit(str(error)) from None
        provider = GeminiProvider(
            api_key,
            model,
            min_seconds_between_calls=min_seconds_between_calls,
            max_calls=max_calls_per_run,
        )
        cache_path = CACHE_DIR / (
            "gemini-" + hashlib.sha256(model.encode("utf-8")).hexdigest()[:12] + ".json"
        )
        cache = EvaluationCache(cache_path, model, held_out_cases)
        try:
            live = evaluate_gemini(
                held_out_cases,
                engine,
                provider,
                cache,
                retry_failed=not args.no_retry_failed,
            )
        except EvaluationPaused as error:
            print(str(error))
            print(
                f"Rerun the same command to continue from cached outcomes. "
                f"Cache file: {cache_path.relative_to(PROJECT_ROOT)}"
            )
            raise SystemExit(2) from None

    write_results(train_cases, held_out_cases, rules, live, model, cache)
    print(
        f"Cases: {len(cases)} synthetic "
        f"({len(train_cases)} training; {len(held_out_cases)} held out)"
    )
    print(f"Mode: {'rules-only' if live is None else f'live Gemini / {model}'}")
    if live is not None:
        print(
            f"Gemini cache: {live.cache_hits} hits, {live.cache_misses} misses, "
            f"{live.api_attempts} API attempts"
        )
    print(f"Results written to {RESULTS_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
