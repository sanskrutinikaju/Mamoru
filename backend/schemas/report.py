"""User-facing Safety Report schema."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

SafetyLevel = Literal["Low", "Medium", "High", "Cannot tell"]
ConfidenceLevel = Literal["Low", "Medium", "High"]
FindingSource = Literal["rule", "llm", "rule_and_llm"]


class SafetyReportFinding(BaseModel):
    """A concise explanation of one signal and its supporting evidence."""

    model_config = ConfigDict(extra="forbid", strict=True)

    category: str
    severity: Literal["Low", "Medium", "High"]
    evidence: str
    explanation: str
    confidence: ConfidenceLevel
    source: FindingSource


class SafetyReport(BaseModel):
    """Overall level and findings, including an explicit cannot-tell outcome."""

    model_config = ConfigDict(extra="forbid", strict=True)

    overallLevel: SafetyLevel
    explanation: str
    findings: list[SafetyReportFinding]
