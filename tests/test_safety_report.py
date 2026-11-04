from backend.reporting import build_safety_report
from backend.rules import RuleEngine
from backend.schemas.analysis import LLMFinding


def test_no_findings_produces_explicit_cannot_tell_report():
    report = build_safety_report([], [])

    assert report.overallLevel == "Cannot tell"
    assert "cannot tell" in report.explanation.lower()
    assert report.findings == []


def test_highest_finding_severity_sets_overall_level():
    findings = RuleEngine().analyze(
        "Act now: click this link to verify your account. "
        "Please enter your account password."
    )

    report = build_safety_report(findings, [])

    assert report.overallLevel == "High"
    assert report.findings
    assert all(finding.confidence == "Medium" for finding in report.findings)


def test_agreeing_rule_and_llm_findings_merge_with_high_confidence():
    rule_finding = RuleEngine().analyze("Please enter your account password.")[0]
    llm_finding = LLMFinding(
        category="credential_request",
        severity="High",
        evidence=rule_finding.evidence,
        explanation="This text requests a password.",
    )

    report = build_safety_report([rule_finding], [llm_finding])

    assert report.overallLevel == "High"
    assert len(report.findings) == 1
    assert report.findings[0].source == "rule_and_llm"
    assert report.findings[0].confidence == "High"


def test_low_severity_finding_produces_low_overall_level():
    finding = LLMFinding(
        category="urgency_pressure",
        severity="Low",
        evidence="sample quote",
        explanation="Synthetic low-severity explanation.",
    )

    report = build_safety_report([], [finding])

    assert report.overallLevel == "Low"
    assert report.findings[0].confidence == "Low"


def test_medium_finding_sets_medium_when_no_high_finding_exists():
    findings = RuleEngine().analyze("Act now: a synthetic offer ends today.")

    report = build_safety_report(findings, [])

    assert report.overallLevel == "Medium"
