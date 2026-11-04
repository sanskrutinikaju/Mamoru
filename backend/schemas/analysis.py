"""Strict schemas for structured LLM output."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ThreatCategory = Literal[
    "credential_request",
    "urgency_pressure",
    "prompt_injection",
    "deceptive_link",
]


class LLMFinding(BaseModel):
    """One LLM-identified signal with a quote that must occur in page text."""

    model_config = ConfigDict(extra="forbid", strict=True)

    category: ThreatCategory
    severity: Literal["Low", "Medium", "High"]
    evidence: str = Field(min_length=1, max_length=300)
    explanation: str = Field(min_length=1, max_length=500)


class LLMAnalysis(BaseModel):
    """Validated JSON object returned by the single configured LLM."""

    model_config = ConfigDict(extra="forbid", strict=True)

    findings: list[LLMFinding] = Field(max_length=10)
