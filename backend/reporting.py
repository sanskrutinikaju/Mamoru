"""Build a cautious Safety Report from validated rule and LLM findings."""

from dataclasses import dataclass

from backend.rules.detector import Finding as RuleEngineFinding
from backend.schemas.analysis import LLMFinding
from backend.schemas.report import SafetyReport, SafetyReportFinding

SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3}


@dataclass(frozen=True)
class ReportInput:
    category: str
    severity: str
    evidence: str
    explanation: str
    source: str


def build_safety_report(
    rule_findings: list[RuleEngineFinding],
    llm_findings: list[LLMFinding],
) -> SafetyReport:
    """Merge matching categories and use the strongest observed severity."""
    entries: list[ReportInput] = [
        ReportInput(
            category=finding.category,
            severity=finding.severity,
            evidence=finding.evidence,
            explanation=finding.description,
            source="rule",
        )
        for finding in rule_findings
    ]
    entries.extend(
        ReportInput(
            category=finding.category,
            severity=finding.severity,
            evidence=finding.evidence,
            explanation=finding.explanation,
            source="llm",
        )
        for finding in llm_findings
    )

    merged: dict[tuple[str, str], ReportInput] = {}
    sources: dict[tuple[str, str], set[str]] = {}
    for entry in entries:
        key = (entry.category, entry.evidence)
        existing = merged.get(key)
        if existing is None:
            merged[key] = entry
            sources[key] = {entry.source}
            continue

        sources[key].add(entry.source)
        stronger = (
            entry
            if SEVERITY_RANK[entry.severity] > SEVERITY_RANK[existing.severity]
            else existing
        )
        merged[key] = ReportInput(
            category=existing.category,
            severity=stronger.severity,
            evidence=existing.evidence,
            explanation=(
                existing.explanation
                if existing.source == "rule"
                else entry.explanation
            ),
            source="rule_and_llm",
        )

    report_findings = [
        SafetyReportFinding(
            category=entry.category,
            severity=entry.severity,
            evidence=entry.evidence,
            explanation=entry.explanation,
            confidence=_confidence_for_sources(sources[key]),
            source=(
                "rule_and_llm"
                if sources[key] == {"rule", "llm"}
                else entry.source
            ),
        )
        for key, entry in merged.items()
    ]

    if not report_findings:
        return SafetyReport(
            overallLevel="Cannot tell",
            explanation=(
                "No configured signal was found. Mamoru cannot tell whether "
                "this page is safe."
            ),
            findings=[],
        )

    overall_level = max(
        (finding.severity for finding in report_findings),
        key=SEVERITY_RANK.__getitem__,
    )
    return SafetyReport(
        overallLevel=overall_level,
        explanation=_overall_explanation(overall_level),
        findings=report_findings,
    )


def _confidence_for_sources(sources: set[str]) -> str:
    if sources == {"rule", "llm"}:
        return "High"
    if sources == {"rule"}:
        return "Medium"
    return "Low"


def _overall_explanation(level: str) -> str:
    explanations = {
        "High": "At least one high-severity signal was found. Review the evidence carefully.",
        "Medium": "Medium-severity signals were found. Review the evidence before proceeding.",
        "Low": "Only low-severity signals were found. This is not a guarantee of safety.",
    }
    return explanations[level]
