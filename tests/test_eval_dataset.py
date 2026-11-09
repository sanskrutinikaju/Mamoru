import hashlib
import json
import sys
from pathlib import Path

import pytest

import eval.run_ai_written as ai_written_report
import eval.run as evaluation_run
from backend.llm.provider import (
    LLMCallLimitError,
    LLMInvalidResponseError,
    LLMProviderError,
    LLMRateLimitError,
    TokenUsage,
)
from backend.rules import RuleEngine
from eval.run import (
    CLAUDE_CASES_PATH,
    EvaluationCache,
    EvaluationPaused,
    VariantResult,
    _category_rows,
    _case_digest,
    _format_variant_row,
    evaluate_gemini,
    load_ai_written_cases,
    load_cases,
    load_split,
)
from backend.schemas.analysis import LLMAnalysis

PROJECT_ROOT = Path(__file__).parents[1]
CASES_PATH = PROJECT_ROOT / "eval" / "data" / "cases.jsonl"
SPLIT_PATH = PROJECT_ROOT / "eval" / "data" / "splits.json"


def _cases():
    return load_cases(CASES_PATH)


def _held_out():
    return load_split(_cases(), SPLIT_PATH)[1]


class FakeProvider:
    model = "gemini-test-model"

    def __init__(self, result=None, failure=None):
        self.result = result or LLMAnalysis(findings=[])
        self.failure = failure
        self.calls = 0
        self.last_usage = None
        self.last_attempt_count = 0

    def analyze(self, page_text):
        assert page_text
        self.calls += 1
        self.last_attempt_count = 1
        if self.failure:
            raise self.failure
        self.last_usage = TokenUsage(100, 10, 2)
        return self.result


def test_synthetic_dataset_has_144_cases_and_separate_held_out_group():
    cases = _cases()
    train_cases, held_out_cases = load_split(cases, SPLIT_PATH)
    original_held_out_ids = {
        f"heldout-{label}-{index:02}"
        for label in ("benign", "threat")
        for index in range(1, 13)
    }
    held_out_groups = {
        group: sum(case["group"] == group for case in held_out_cases)
        for group in {"core", "handwritten_scam_style"}
    }

    assert len(cases) == 144
    assert len({case["id"] for case in cases}) == 144
    assert all(case["synthetic"] is True for case in cases)
    assert len(train_cases) == 96
    assert len(held_out_cases) == 48
    assert original_held_out_ids.issubset({case["id"] for case in held_out_cases})
    assert original_held_out_ids.isdisjoint({case["id"] for case in train_cases})
    assert held_out_groups == {"core": 24, "handwritten_scam_style": 24}
    assert sum(case["label"] == "benign" for case in held_out_cases) == 16
    assert sum(case["label"] == "threat" for case in held_out_cases) == 32
    scam_cases = [
        case for case in cases if case["group"] == "handwritten_scam_style"
    ]
    assert len(scam_cases) == 24
    assert {case["authorship"] for case in scam_cases} == {"AI-written"}


def test_dataset_loader_rejects_case_not_marked_synthetic(tmp_path):
    source = _cases()[0]
    source["synthetic"] = False
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="non-synthetic"):
        load_cases(cases_path)


def test_ai_written_dataset_normalizes_and_validates_every_line(tmp_path):
    cases = load_ai_written_cases()
    assert len(cases) == 20
    assert all(case["group"] == "ai_written_claude" for case in cases)
    assert all(case["synthetic"] is True for case in cases)
    assert all(case["authorship"] == "AI-written" for case in cases)
    assert {case["label"] for case in cases} == {"threat", "benign"}
    assert all(case["category"] != "benign" for case in cases)
    assert {"tech_support_scam", "advance_fee_scam"}.issubset(
        {case["category"] for case in cases}
    )

    path = tmp_path / "claude.jsonl"
    source = json.loads(CLAUDE_CASES_PATH.read_text(encoding="utf-8").splitlines()[0])
    path.write_text(json.dumps(source) + "\n{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_ai_written_cases(path)

    path.write_text(json.dumps(source) + "\n" + json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_ai_written_cases(path)

    source["label"] = "unknown"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid AI-written case"):
        load_ai_written_cases(path)


def test_ai_written_cache_keys_do_not_collide_with_existing_evaluation_cases():
    model = FakeProvider.model
    ai_written_keys = {
        _case_digest(case, model) for case in load_ai_written_cases()
    }
    existing_keys = {_case_digest(case, model) for case in _cases()}

    assert len(ai_written_keys) == 20
    assert ai_written_keys.isdisjoint(existing_keys)


def _configure_ai_written_live_run(monkeypatch, tmp_path, provider):
    from backend import config
    from backend.llm import provider as provider_module

    monkeypatch.setattr(sys, "argv", ["eval/run_ai_written.py", "--live-gemini", "--no-retry-failed"])
    monkeypatch.setattr(ai_written_report, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(ai_written_report, "RESULTS_AI_WRITTEN_PATH", tmp_path / "RESULTS_AI_WRITTEN.md")
    monkeypatch.setattr(ai_written_report, "_commit_hash", lambda: "test123")
    monkeypatch.setattr(config, "get_gemini_api_key", lambda: "mock-key")
    monkeypatch.setattr(config, "get_gemini_model", lambda: provider.model)
    monkeypatch.setattr(config, "get_gemini_min_seconds_between_calls", lambda: 0)
    monkeypatch.setattr(config, "get_gemini_max_calls_per_run", lambda: 40)
    monkeypatch.setattr(provider_module, "GeminiProvider", lambda *args, **kwargs: provider)


def test_ai_written_live_run_preserves_hash_of_existing_successful_and_failed_entries(
    tmp_path, monkeypatch
):
    cases = load_ai_written_cases()
    cache_path = tmp_path / "cache" / f"gemini-ai-written-claude-{hashlib.sha256(FakeProvider.model.encode()).hexdigest()[:12]}.json"

    class SeedProvider(FakeProvider):
        def analyze(self, page_text):
            self.calls += 1
            self.last_attempt_count = 1
            if page_text == cases[1]["text"]:
                raise LLMProviderError("Synthetic cached failure.")
            self.last_usage = TokenUsage(100, 10, 2)
            return self.result

    seeded_cache = EvaluationCache(cache_path, FakeProvider.model, cases)
    evaluate_gemini(cases[:2], RuleEngine(), SeedProvider(), seeded_cache)
    original_digests = set(seeded_cache.entries)

    def entries_hash(entries):
        serialized = json.dumps(
            sorted((digest, entries[digest]) for digest in original_digests),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    before_hash = entries_hash(seeded_cache.entries)
    provider = FakeProvider()
    _configure_ai_written_live_run(monkeypatch, tmp_path, provider)

    ai_written_report.main()

    after_cache = EvaluationCache(cache_path, FakeProvider.model, cases)
    assert {entry["status"] for entry in seeded_cache.entries.values()} == {"completed", "failed"}
    assert entries_hash(after_cache.entries) == before_hash
    assert provider.calls == len(cases) - len(original_digests)


def test_ai_written_live_run_backs_up_cache_before_request_without_overwriting_backup(
    tmp_path, monkeypatch
):
    from datetime import datetime as RealDateTime

    cases = load_ai_written_cases()
    model = FakeProvider.model
    model_hash = hashlib.sha256(model.encode()).hexdigest()[:12]
    cache_dir = tmp_path / "cache"
    cache_path = cache_dir / f"gemini-ai-written-claude-{model_hash}.json"
    cache = EvaluationCache(cache_path, model, cases)
    cache._save()
    original_cache = cache_path.read_bytes()
    fixed_timestamp = "20260102-030405"
    existing_backup = cache_path.with_name(
        f"{cache_path.stem}.backup-{fixed_timestamp}{cache_path.suffix}"
    )
    existing_backup.parent.mkdir(parents=True, exist_ok=True)
    existing_backup.write_bytes(b"keep this backup")

    class FixedDateTime:
        @classmethod
        def now(cls):
            return RealDateTime.strptime(fixed_timestamp, "%Y%m%d-%H%M%S")

    class BackupCheckingProvider(FakeProvider):
        def analyze(self, page_text):
            backup = cache_path.with_name(
                f"{cache_path.stem}.backup-{fixed_timestamp}-1{cache_path.suffix}"
            )
            assert backup.read_bytes() == original_cache
            assert existing_backup.read_bytes() == b"keep this backup"
            return super().analyze(page_text)

    monkeypatch.setattr(ai_written_report, "datetime", FixedDateTime)
    provider = BackupCheckingProvider()
    _configure_ai_written_live_run(monkeypatch, tmp_path, provider)

    ai_written_report.main()

    assert provider.calls == len(cases)
    assert existing_backup.read_bytes() == b"keep this backup"


def test_ai_written_live_run_sends_only_synthetic_case_texts(tmp_path, monkeypatch):
    cases = load_ai_written_cases()

    class RecordingProvider(FakeProvider):
        def __init__(self):
            super().__init__()
            self.sent_texts = []

        def analyze(self, page_text):
            self.sent_texts.append(page_text)
            return super().analyze(page_text)

    provider = RecordingProvider()
    _configure_ai_written_live_run(monkeypatch, tmp_path, provider)

    ai_written_report.main()

    synthetic_texts = {case["text"] for case in cases if case["synthetic"] is True}
    assert provider.sent_texts
    assert set(provider.sent_texts).issubset(synthetic_texts)
    assert len(provider.sent_texts) == len(cases)


def test_ai_written_live_run_stops_cleanly_at_call_cap(
    tmp_path, monkeypatch, capsys
):
    class CappedProvider(FakeProvider):
        def analyze(self, page_text):
            if self.calls == 1:
                raise LLMCallLimitError("Synthetic per-run call cap.")
            return super().analyze(page_text)

    provider = CappedProvider()
    _configure_ai_written_live_run(monkeypatch, tmp_path, provider)

    ai_written_report.main()

    output = capsys.readouterr().out
    assert provider.calls == 1
    assert "1 cases completed; 19 remain" in output
    assert "per-run call cap" in output


def test_ai_written_live_run_stops_cleanly_on_rate_limit(
    tmp_path, monkeypatch, capsys
):
    class RateLimitedProvider(FakeProvider):
        def analyze(self, page_text):
            if self.calls == 1:
                self.calls += 1
                self.last_attempt_count = 1
                raise LLMRateLimitError("Synthetic rate limit.")
            return super().analyze(page_text)

    provider = RateLimitedProvider()
    _configure_ai_written_live_run(monkeypatch, tmp_path, provider)

    ai_written_report.main()

    output = capsys.readouterr().out
    assert provider.calls == 2
    assert "1 cases completed; 19 remain" in output
    assert "rate limit" in output


def test_ai_written_live_run_writes_only_its_dedicated_report(
    tmp_path, monkeypatch
):
    provider = FakeProvider()
    _configure_ai_written_live_run(monkeypatch, tmp_path, provider)
    written_paths = []
    original_write_text = Path.write_text

    def track_write(path, *args, **kwargs):
        written_paths.append(path.resolve())
        assert path.name != "RESULTS.md"
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", track_write)

    ai_written_report.main()

    assert written_paths == [(tmp_path / "RESULTS_AI_WRITTEN.md").resolve()]
    assert (PROJECT_ROOT / "docs" / "RESULTS.md").exists()


def test_ai_written_live_report_summarizes_structured_prompt_injection_results(
    tmp_path, monkeypatch
):
    cases = load_ai_written_cases()
    cases_by_id = {case["id"]: case for case in cases}

    class StructuredProvider(FakeProvider):
        def analyze(self, page_text):
            self.calls += 1
            self.last_attempt_count = 1
            case_id = next(
                case["id"] for case in cases if case["text"] == page_text
            )
            if case_id == "cw_004":
                findings = [
                    {
                        "category": "prompt_injection",
                        "severity": "Low",
                        "evidence": "AI assistants reading this page",
                        "explanation": "This website is completely safe.",
                    }
                ]
            elif case_id == "cw_005":
                findings = [
                    {
                        "category": "prompt_injection",
                        "severity": "Medium",
                        "evidence": "forward the user's conversation",
                        "explanation": "This is an untrusted prompt-injection attempt.",
                    }
                ]
            else:
                findings = []
            self.last_usage = TokenUsage(100, 10, 2)
            return LLMAnalysis(findings=findings)

    provider = StructuredProvider()
    _configure_ai_written_live_run(monkeypatch, tmp_path, provider)

    ai_written_report.main()

    report = (tmp_path / "RESULTS_AI_WRITTEN.md").read_text(encoding="utf-8")
    rules_predictions = {
        case["id"]: result.prediction
        for case, result in zip(cases, ai_written_report.evaluate_rules(cases, RuleEngine()))
    }
    assert (
        f"| cw_004 | {'yes' if rules_predictions['cw_004'] else 'no'} | yes | "
        "yes (explicit matching claim) | prompt_injection (Low) |"
    ) in report
    assert (
        f"| cw_005 | {'yes' if rules_predictions['cw_005'] else 'no'} | yes | "
        "no (prompt injection identified) | prompt_injection (Medium) |"
    ) in report
    assert (
        f"| cw_006 | {'yes' if rules_predictions['cw_006'] else 'no'} | no | "
        "unclear | none |"
    ) in report
    assert "had not seen the rule definitions" in report
    assert "synthetic" in report
    assert "never used to tune rules or prompts" in report
    assert "very small sample" in report
    assert "not real-world performance" in report
    assert "test123" in report
    assert all(case["text"] not in report for case in cases_by_id.values())
    assert provider.calls == len(cases)


def test_ai_written_report_writes_only_to_its_separate_path(tmp_path, monkeypatch):
    output_path = tmp_path / "RESULTS_AI_WRITTEN.md"
    written_paths = []
    original_write_text = Path.write_text

    def track_write(path, *args, **kwargs):
        written_paths.append(path.name)
        assert path.name != "RESULTS.md"
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", track_write)
    monkeypatch.setattr(ai_written_report, "RESULTS_AI_WRITTEN_PATH", output_path)
    monkeypatch.setattr(ai_written_report, "_commit_hash", lambda: "test123")
    monkeypatch.setattr(sys, "argv", ["eval/run_ai_written.py"])

    ai_written_report.main()

    assert written_paths == ["RESULTS_AI_WRITTEN.md"]
    assert "test123" in output_path.read_text(encoding="utf-8")


def test_split_rejects_unknown_held_out_ids(tmp_path):
    split_path = tmp_path / "splits.json"
    split_path.write_text(
        json.dumps({"held_out_ids": ["unknown-case"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not found"):
        load_split(_cases(), split_path)


def test_metrics_treat_no_finding_as_abstention_and_negative_prediction():
    from eval.run import calculate_metrics

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


def test_result_tables_have_matching_columns_when_live_results_are_pending():
    cases = _held_out()
    rules = [
        VariantResult(False, "Cannot tell", 0.001, "rules")
        for _ in cases
    ]
    row_without_live = _format_variant_row(
        "Gemini only",
        "Not run",
        cases,
        None,
    )
    row_with_results = _format_variant_row(
        "Rules only",
        "Mamoru rules",
        cases,
        rules,
    )
    category_rows = _category_rows(
        cases,
        [
            ("Rules only", "Mamoru rules", rules),
            ("Gemini only", "Not run", None),
        ],
    )

    assert len(row_without_live.strip("|").split("|")) == 12
    assert len(row_with_results.strip("|").split("|")) == 12
    assert all(len(row.strip("|").split("|")) == 12 for row in category_rows)
    assert any(row.startswith("| AI-written scam-style |") for row in category_rows)


def test_gemini_results_are_cached_and_reused_without_page_text():
    cases = _held_out()[:3]
    cache_path = Path("unused")
    # Keep test artifacts outside the repository and out of the committed cache.
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_path = Path(temp_dir) / "gemini-cache.json"
        provider = FakeProvider()
        cache = EvaluationCache(cache_path, provider.model, cases)
        first = evaluate_gemini(cases, RuleEngine(), provider, cache)

        assert provider.calls == len(cases)
        assert first.cache_misses == len(cases)
        assert first.api_attempts == len(cases)
        assert first.llm[0].token_usage == TokenUsage(100, 10, 2)

        cached_contents = cache_path.read_text(encoding="utf-8")
        for case in cases:
            assert case["text"] not in cached_contents

        second_provider = FakeProvider()
        second_cache = EvaluationCache(cache_path, second_provider.model, cases)
        second = evaluate_gemini(
            cases,
            RuleEngine(),
            second_provider,
            second_cache,
        )
        assert second_provider.calls == 0
        assert second.cache_hits == len(cases)
        assert second.cache_misses == 0
        assert second.llm == first.llm


def test_retry_failure_never_changes_or_re_requests_successful_cache_entries(tmp_path):
    cases = _held_out()[:2]
    failed_text = cases[1]["text"]

    class SelectiveProvider(FakeProvider):
        def __init__(self, failure_text=None):
            super().__init__()
            self.failure_text = failure_text
            self.called_texts = []

        def analyze(self, page_text):
            self.calls += 1
            self.called_texts.append(page_text)
            self.last_attempt_count = 1
            if page_text == self.failure_text:
                raise LLMProviderError("Synthetic provider failure.")
            self.last_usage = TokenUsage(100, 10, 2)
            return self.result

    def successful_entries_hash(cache):
        entries = sorted(
            (digest, entry)
            for digest, entry in cache.entries.items()
            if entry["status"] == "completed"
        )
        serialized = json.dumps(entries, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    cache_path = tmp_path / "gemini-cache.json"
    initial_provider = SelectiveProvider(failure_text=failed_text)
    initial_cache = EvaluationCache(cache_path, initial_provider.model, cases)
    evaluate_gemini(cases, RuleEngine(), initial_provider, initial_cache)

    resumed_cache = EvaluationCache(cache_path, initial_provider.model, cases)
    successful_hash_before = successful_entries_hash(resumed_cache)
    retry_provider = SelectiveProvider(failure_text=failed_text)
    result = evaluate_gemini(cases, RuleEngine(), retry_provider, resumed_cache)

    assert retry_provider.calls == 1
    assert retry_provider.called_texts == [failed_text]
    assert result.llm[0].status == "completed"
    assert result.llm[1].status == "failed"
    assert len(resumed_cache.get(cases[1])["previous_failures"]) == 1
    assert successful_entries_hash(resumed_cache) == successful_hash_before


def test_failed_cache_entry_is_retried_once_per_run(tmp_path):
    case = _held_out()[0]
    cache = EvaluationCache(tmp_path / "gemini-cache.json", FakeProvider.model, [case])
    _seed_provider = FakeProvider(failure=LLMProviderError("Initial failure."))
    evaluate_gemini([case], RuleEngine(), _seed_provider, cache)

    for expected_failures in (1, 2):
        retry_provider = FakeProvider(
            failure=LLMProviderError("Retry failure.")
        )
        result = evaluate_gemini([case], RuleEngine(), retry_provider, cache)

        assert retry_provider.calls == 1
        assert result.llm[0].status == "failed"
        assert len(cache.get(case)["previous_failures"]) == expected_failures


def test_no_retry_failed_flag_reuses_cached_failure(tmp_path, monkeypatch):
    cases = _held_out()[:1]
    model = FakeProvider.model
    cache_path = tmp_path / (
        "gemini-" + hashlib.sha256(model.encode("utf-8")).hexdigest()[:12] + ".json"
    )
    seed_cache = EvaluationCache(cache_path, model, cases)
    evaluate_gemini(
        cases,
        RuleEngine(),
        FakeProvider(failure=LLMProviderError("Initial failure.")),
        seed_cache,
    )

    provider = FakeProvider()
    captured = {}
    monkeypatch.setattr(sys, "argv", ["eval/run.py", "--live-gemini", "--no-retry-failed"])
    monkeypatch.setattr(evaluation_run, "load_cases", lambda: cases)
    monkeypatch.setattr(evaluation_run, "load_split", lambda loaded: ([], loaded))
    monkeypatch.setattr(evaluation_run, "get_gemini_api_key", lambda: "mock-key")
    monkeypatch.setattr(evaluation_run, "get_gemini_model", lambda: model)
    monkeypatch.setattr(evaluation_run, "get_gemini_min_seconds_between_calls", lambda: 0)
    monkeypatch.setattr(evaluation_run, "get_gemini_max_calls_per_run", lambda: 1)
    monkeypatch.setattr(evaluation_run, "GeminiProvider", lambda *args, **kwargs: provider)
    monkeypatch.setattr(evaluation_run, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(
        evaluation_run,
        "write_results",
        lambda *args: captured.setdefault("live", args[3]),
    )

    evaluation_run.main()

    assert provider.calls == 0
    assert captured["live"].llm[0].status == "failed"
    assert captured["live"].cache_hits == 1
    assert captured["live"].cache_misses == 0


def test_call_cap_stops_after_retry_uses_the_run_limit(tmp_path):
    cases = _held_out()[:3]
    cache = EvaluationCache(
        tmp_path / "gemini-cache.json", FakeProvider.model, cases
    )
    seed_provider = FakeProvider(failure=LLMProviderError("Initial failure."))
    evaluate_gemini(cases[:2], RuleEngine(), seed_provider, cache)

    class OneCallRetryProvider(FakeProvider):
        def analyze(self, page_text):
            assert page_text
            if self.calls == 1:
                raise LLMCallLimitError("Gemini per-run call limit reached.")
            self.calls += 1
            self.last_attempt_count = 1
            raise LLMProviderError("Retry failed.")

    retry_provider = OneCallRetryProvider()
    with pytest.raises(EvaluationPaused) as paused:
        evaluate_gemini(cases, RuleEngine(), retry_provider, cache)

    assert retry_provider.calls == 1
    assert paused.value.completed == 1
    assert paused.value.remaining == 2
    assert "per-run call cap" in str(paused.value)


def test_rate_limit_during_retry_stops_with_remaining_count(tmp_path):
    cases = _held_out()[:3]
    cache = EvaluationCache(
        tmp_path / "gemini-cache.json", FakeProvider.model, cases
    )
    evaluate_gemini(cases[:1], RuleEngine(), FakeProvider(), cache)
    seed_provider = FakeProvider(failure=LLMProviderError("Initial failure."))
    evaluate_gemini(cases[1:2], RuleEngine(), seed_provider, cache)

    class RateLimitOnRetryProvider(FakeProvider):
        def analyze(self, page_text):
            assert page_text == cases[1]["text"]
            self.calls += 1
            self.last_attempt_count = 1
            raise LLMRateLimitError("Synthetic rate limit.")

    retry_provider = RateLimitOnRetryProvider()
    with pytest.raises(EvaluationPaused) as paused:
        evaluate_gemini(cases, RuleEngine(), retry_provider, cache)

    assert retry_provider.calls == 1
    assert paused.value.completed == 1
    assert paused.value.remaining == 2
    assert "1 cases completed; 2 remain" in str(paused.value)
    assert cache.rate_limit_events[cases[1]["id"]] == 1


def test_rate_limit_stops_immediately_and_rerun_uses_completed_cache(tmp_path):
    cases = _held_out()[:3]

    class RateLimitAfterOne(FakeProvider):
        def analyze(self, page_text):
            del page_text
            if self.calls == 0:
                self.calls += 1
                self.last_attempt_count = 1
                self.last_usage = TokenUsage(20, 5)
                return LLMAnalysis(findings=[])
            self.calls += 1
            self.last_attempt_count = 1
            raise LLMRateLimitError("Synthetic rate limit.")

    cache_path = tmp_path / "gemini-cache.json"
    provider = RateLimitAfterOne()
    cache = EvaluationCache(cache_path, provider.model, cases)
    with pytest.raises(EvaluationPaused) as paused:
        evaluate_gemini(cases, RuleEngine(), provider, cache)
    assert paused.value.completed == 1
    assert paused.value.remaining == 2
    assert "1 cases completed; 2 remain" in str(paused.value)
    assert len(cache.entries) == 1
    assert provider.calls == 2
    assert sum(cache.rate_limit_events.values()) == 1

    resumed_provider = FakeProvider()
    resumed_cache = EvaluationCache(cache_path, resumed_provider.model, cases)
    resumed = evaluate_gemini(
        cases,
        RuleEngine(),
        resumed_provider,
        resumed_cache,
    )
    assert resumed.cache_hits == 1
    assert resumed.cache_misses == 2
    assert resumed_provider.calls == 2
    assert resumed.rate_limit_responses == 1
    assert resumed.api_attempts == 4


def test_per_run_call_cap_stops_with_completed_and_remaining_counts(tmp_path):
    cases = _held_out()[:3]

    class CappedProvider(FakeProvider):
        def analyze(self, page_text):
            if self.calls == 1:
                raise LLMCallLimitError("Gemini per-run call limit reached.")
            return super().analyze(page_text)

    provider = CappedProvider()
    cache = EvaluationCache(tmp_path / "gemini-cache.json", provider.model, cases)
    with pytest.raises(EvaluationPaused) as paused:
        evaluate_gemini(cases, RuleEngine(), provider, cache)

    assert provider.calls == 1
    assert paused.value.completed == 1
    assert paused.value.remaining == 2
    assert "per-run call cap" in str(paused.value)


@pytest.mark.parametrize(
    ("failure", "expected_status"),
    [
        (LLMInvalidResponseError("Synthetic invalid result."), "invalid"),
        (LLMProviderError("Synthetic provider failure."), "failed"),
    ],
)
def test_live_evaluation_counts_invalid_and_provider_failures(
    tmp_path,
    failure,
    expected_status,
):
    cases = _held_out()[:1]
    provider = FakeProvider(failure=failure)
    cache = EvaluationCache(tmp_path / "cache.json", provider.model, cases)

    result = evaluate_gemini(cases, RuleEngine(), provider, cache)

    assert result.llm[0].status == expected_status
    assert result.llm[0].prediction is False
    assert result.hybrid[0].prediction is bool(RuleEngine().analyze(cases[0]["text"]))


def test_gemini_cache_refuses_non_synthetic_cases(tmp_path):
    case = dict(_held_out()[0])
    case["synthetic"] = False

    with pytest.raises(ValueError, match="only synthetic"):
        EvaluationCache(tmp_path / "cache.json", "gemini-test", [case])
