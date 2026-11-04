"""Apply minimization, validate evidence, and preserve deterministic rule floors."""

import logging
from dataclasses import dataclass
from typing import Literal

from backend.config import MAX_LLM_CONTENT_CHARS, get_openai_api_key, get_openai_model
from backend.rules.detector import Finding
from backend.schemas.analysis import LLMAnalysis, LLMFinding

from .provider import LLMProvider, LLMProviderError, OpenAIProvider

logger = logging.getLogger("mamoru.llm")

LLMStatus = Literal["completed", "unavailable", "failed"]
SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3}


@dataclass(frozen=True)
class LLMServiceResult:
    status: LLMStatus
    message: str
    findings: list[LLMFinding]


class LLMService:
    """Run one provider with explicit, privacy-safe deterministic fallback."""

    def __init__(self, provider: LLMProvider | None) -> None:
        self.provider = provider

    @classmethod
    def from_environment(cls) -> "LLMService":
        api_key = get_openai_api_key()
        if not api_key:
            return cls(provider=None)
        return cls(
            provider=OpenAIProvider(
                api_key=api_key,
                model=get_openai_model(),
            )
        )

    @staticmethod
    def _apply_rule_severity_floor(
        findings: list[LLMFinding],
        rule_findings: list[Finding],
    ) -> list[LLMFinding]:
        floors: dict[str, str] = {}
        for rule_finding in rule_findings:
            current = floors.get(rule_finding.category, "Low")
            if SEVERITY_RANK[rule_finding.severity] > SEVERITY_RANK[current]:
                floors[rule_finding.category] = rule_finding.severity

        adjusted: list[LLMFinding] = []
        for finding in findings:
            floor = floors.get(finding.category)
            if floor and SEVERITY_RANK[finding.severity] < SEVERITY_RANK[floor]:
                finding = finding.model_copy(update={"severity": floor})
            adjusted.append(finding)
        return adjusted

    def analyze(
        self,
        page_text: str,
        rule_findings: list[Finding],
    ) -> LLMServiceResult:
        if self.provider is None:
            return LLMServiceResult(
                status="unavailable",
                message=(
                    "OpenAI is not configured. Deterministic rule findings only "
                    "are returned."
                ),
                findings=[],
            )

        minimized_text = page_text[:MAX_LLM_CONTENT_CHARS]
        try:
            analysis: LLMAnalysis = self.provider.analyze(minimized_text)
        except LLMProviderError:
            logger.warning("LLM analysis failed; returning deterministic findings only.")
            return LLMServiceResult(
                status="failed",
                message=(
                    "OpenAI analysis failed. Deterministic rule findings only "
                    "are returned."
                ),
                findings=[],
            )

        try:
            return self.process_analysis(
                minimized_text,
                analysis,
                rule_findings,
            )
        except LLMProviderError:
            logger.warning("LLM analysis failed validation; returning deterministic findings only.")
            return LLMServiceResult(
                status="failed",
                message=(
                    "OpenAI analysis failed validation. Deterministic rule "
                    "findings only are returned."
                ),
                findings=[],
            )

    @classmethod
    def process_analysis(
        cls,
        page_text: str,
        analysis: LLMAnalysis,
        rule_findings: list[Finding],
    ) -> LLMServiceResult:
        """Validate one provider result and optionally apply deterministic floors."""
        minimized_text = page_text[:MAX_LLM_CONTENT_CHARS]
        if any(finding.evidence not in minimized_text for finding in analysis.findings):
            raise LLMProviderError(
                "The OpenAI response included evidence not present in the input."
            )
        return LLMServiceResult(
            status="completed",
            message="OpenAI analysis completed; deterministic rule severity is the minimum.",
            findings=cls._apply_rule_severity_floor(
                analysis.findings,
                rule_findings,
            ),
        )


def create_llm_service() -> LLMService:
    """Create the configured single-provider service."""
    return LLMService.from_environment()
