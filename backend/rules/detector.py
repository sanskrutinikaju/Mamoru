"""Deterministic text rules for common phishing and prompt-injection signals."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Severity = Literal["Low", "Medium", "High"]
RULES_PATH = Path(__file__).with_name("rules.json")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    severity: Severity
    category: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class Finding:
    rule_id: str
    description: str
    severity: Severity
    category: str
    evidence: str


class RuleEngine:
    """Load fixed rules and return the first exact matching span per rule."""

    def __init__(self) -> None:
        self.rules = self._load_rules()

    @staticmethod
    def _load_rules() -> list[Rule]:
        try:
            with RULES_PATH.open(encoding="utf-8") as rules_file:
                config = json.load(rules_file)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("Unable to load Mamoru rule configuration.") from error

        if not isinstance(config, dict) or not isinstance(config.get("rules"), list):
            raise RuntimeError("Mamoru rule configuration must contain a rules list.")

        rules: list[Rule] = []
        seen_ids: set[str] = set()
        valid_severities = {"Low", "Medium", "High"}
        for item in config["rules"]:
            if not isinstance(item, dict):
                raise RuntimeError("Each Mamoru rule must be an object.")

            rule_id = item.get("id")
            description = item.get("description")
            severity = item.get("severity")
            category = item.get("category")
            pattern_text = item.get("pattern")
            if (
                not isinstance(rule_id, str)
                or not rule_id
                or rule_id in seen_ids
                or not isinstance(description, str)
                or not description
                or not isinstance(severity, str)
                or severity not in valid_severities
                or not isinstance(category, str)
                or not category
                or not isinstance(pattern_text, str)
                or not pattern_text
            ):
                raise RuntimeError("Mamoru rule configuration contains an invalid rule.")

            try:
                pattern = re.compile(pattern_text, re.IGNORECASE)
            except re.error as error:
                raise RuntimeError(
                    f"Mamoru rule '{rule_id}' has an invalid pattern."
                ) from error

            seen_ids.add(rule_id)
            rules.append(
                Rule(
                    rule_id=rule_id,
                    description=description,
                    severity=severity,
                    category=category,
                    pattern=pattern,
                )
            )

        if not rules:
            raise RuntimeError("Mamoru rule configuration must not be empty.")
        return rules

    def analyze(self, content: str) -> list[Finding]:
        """Return at most one finding per rule, using its first matched span."""
        findings: list[Finding] = []
        for rule in self.rules:
            match = rule.pattern.search(content)
            if match:
                findings.append(
                    Finding(
                        rule_id=rule.rule_id,
                        description=rule.description,
                        severity=rule.severity,
                        category=rule.category,
                        evidence=match.group(0),
                    )
                )
        return findings
