import logging

from backend.llm.provider import LLMProviderError
from backend.llm.service import LLMService
from backend.rules import RuleEngine
from backend.schemas.analysis import LLMAnalysis
from backend.schemas.extraction import ExtractionRequest


class FakeProvider:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.received_text = None

    def analyze(self, page_text):
        self.received_text = page_text
        if self.error:
            raise self.error
        return self.result


def test_service_sends_only_capped_text_and_applies_rule_severity_floor():
    content = "A" * 12000 + "NOT_SENT"
    provider = FakeProvider(
        LLMAnalysis(
            findings=[
                {
                    "category": "credential_request",
                    "severity": "Low",
                    "evidence": "A",
                    "explanation": "A sample explanation.",
                }
            ]
        )
    )
    rule_findings = RuleEngine().analyze("Please enter your account password.")

    result = LLMService(provider).analyze(content, rule_findings)

    assert provider.received_text == "A" * 12000
    assert result.status == "completed"
    assert result.findings[0].severity == "High"


def test_service_keeps_llm_result_below_rule_floor_unchanged_when_higher():
    provider = FakeProvider(
        LLMAnalysis(
            findings=[
                {
                    "category": "credential_request",
                    "severity": "High",
                    "evidence": "enter your account password",
                    "explanation": "The text requests a password.",
                }
            ]
        )
    )
    rule_findings = RuleEngine().analyze("Please enter your account password.")

    result = LLMService(provider).analyze(
        "Please enter your account password.",
        rule_findings,
    )

    assert result.findings[0].severity == "High"


def test_service_returns_rules_only_when_provider_is_not_configured():
    result = LLMService(provider=None).analyze("Synthetic text", [])

    assert result.status == "unavailable"
    assert result.findings == []
    assert "Only synthetic evaluation cases" in result.message


def test_service_never_enables_gemini_for_live_page_text(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")

    service = LLMService.from_environment()
    result = service.analyze("Real page content stays local.", [])

    assert service.provider is None
    assert result.status == "unavailable"
    assert "disabled for live page text" in result.message


def test_service_returns_rules_only_after_provider_failure(caplog):
    canary = "SYNTHETIC_LLM_ERROR_CONTENT"
    provider = FakeProvider(error=LLMProviderError(canary))
    caplog.set_level(logging.DEBUG)
    rule_findings = RuleEngine().analyze("Please enter your account password.")

    result = LLMService(provider).analyze(
        f"Please enter your account password. {canary}",
        rule_findings,
    )

    assert result.status == "failed"
    assert result.findings == []
    assert "Deterministic rule findings only" in result.message
    assert canary not in caplog.text
    assert canary not in result.message


def test_service_rejects_evidence_not_in_minimized_page_text():
    provider = FakeProvider(
        LLMAnalysis(
            findings=[
                {
                    "category": "prompt_injection",
                    "severity": "High",
                    "evidence": "invented quote",
                    "explanation": "Synthetic explanation.",
                }
            ]
        )
    )

    result = LLMService(provider).analyze("Only synthetic text.", [])

    assert result.status == "failed"
    assert result.findings == []
    assert "not present in the input" not in result.message


def test_request_validation_content_cap_remains_local():
    request = ExtractionRequest(
        url="https://sample.example.test/",
        title="Synthetic",
        language="en",
        wordCount=1,
        content="x" * 12000,
        consentTimestamp="2026-11-04T00:00:00Z",
    )

    assert len(request.content) == 12000
