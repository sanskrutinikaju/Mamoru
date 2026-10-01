"""
Responsible AI Signal Detector Engine

Analyzes webpage content for signals related to AI transparency, privacy, fairness,
and accountability. No LLM calls. No judgments. Pattern matching only.
"""

import json
import os
from typing import List, Optional, Dict, Any
from .confidence import (
    calculate_keyword_confidence,
    ConfidenceLevel,
)


class ResponsibleAIDetector:
    """
    Main detector engine for responsible AI signals.
    
    Loads rules from JSON configuration and executes pattern matching
    against webpage content. Returns list of signals with confidence.
    
    No LLM. No external API calls. Pattern matching only.
    """
    
    def __init__(self):
        """Initialize detector by loading rules configuration."""
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load rule definitions from rules.json."""
        rules_path = os.path.join(
            os.path.dirname(__file__),
            "rules.json"
        )
        
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return [rule for rule in config.get("rules", []) if rule.get("enabled", True)]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load rules configuration: {e}")
    
    def analyze(
        self,
        content: str,
        url: str,
        title: str = "",
    ) -> List[Dict[str, str]]:
        """
        Analyze webpage content for responsible AI signals.
        
        Args:
            content: Full extracted webpage text
            url: Page URL
            title: Page title
        
        Returns:
            List of signal dictionaries (can be used with Pydantic models)
        """
        signals = []
        analyzed_text = f"{title}\n{url}\n{content}".lower()
        
        for rule in self.rules:
            signal = self._execute_rule(rule, analyzed_text, content)
            if signal:
                signals.append(signal)
        
        return signals
    
    def _execute_rule(
        self,
        rule: Dict[str, Any],
        analyzed_text: str,
        original_content: str,
    ) -> Optional[Dict[str, str]]:
        """
        Execute a single rule against the content.
        
        Returns dictionary if pattern matches, None otherwise.
        Dictionary can be converted to ResponsibleAISignal Pydantic model.
        """
        rule_id = rule.get("ruleId")
        category = rule.get("category")
        patterns = rule.get("patterns", {})
        keywords = patterns.get("keywords", [])
        min_matches = patterns.get("minMatches", 1)
        
        # Check keyword matches
        confidence = calculate_keyword_confidence(
            analyzed_text,
            keywords,
            min_matches,
        )
        
        if not confidence:
            return None
        
        # Collect evidence (matched keywords)
        matched_keywords = [
            kw for kw in keywords
            if kw.lower() in analyzed_text
        ]
        
        # Build evidence string
        evidence = f"Found {len(matched_keywords)} matching signals: {', '.join(matched_keywords[:5])}"
        if len(matched_keywords) > 5:
            evidence += f" and {len(matched_keywords) - 5} more"
        
        # Get rule descriptions
        confidence_rules = rule.get("confidenceRules", {})
        observation = self._generate_observation(
            rule_id,
            category,
            matched_keywords,
        )
        interpretation = confidence_rules.get(
            confidence,
            "Signal detected in content.",
        )
        false_positives = ", ".join(
            rule.get("falsePositives", ["Unknown false positive possibilities"])[:2]
        )
        significance = self._generate_significance(category)
        
        return {
            "signalId": rule_id,
            "category": category,
            "confidence": confidence,
            "evidence": evidence,
            "observation": observation,
            "interpretation": interpretation,
            "falsePossibilities": f"This signal could be inaccurate if: {false_positives}",
            "significance": significance,
        }
    
    def _generate_observation(
        self,
        rule_id: str,
        category: str,
        matched_keywords: List[str],
    ) -> str:
        """Generate factual observation statement based on matched content."""
        observations = {
            "AI_DISCLOSURE_001": f"Content explicitly mentions AI tools or use: {', '.join(matched_keywords[:3])}",
            "TRANSPARENCY_001": f"Content discusses algorithm/methodology: {', '.join(matched_keywords[:3])}",
            "PRIVACY_DATA_001": f"Privacy or data practices mentioned: {', '.join(matched_keywords[:3])}",
            "FAIRNESS_BIAS_001": f"Fairness or bias-related language present: {', '.join(matched_keywords[:3])}",
            "OVERSIGHT_ACCOUNTABILITY_001": f"Oversight or accountability mechanisms mentioned: {', '.join(matched_keywords[:3])}",
            "MANIPULATION_001": f"Personalization or targeting language detected: {', '.join(matched_keywords[:3])}",
            "EVIDENCE_CLAIMS_001": f"AI-driven claims or evidence discussion present: {', '.join(matched_keywords[:3])}",
            "AI_GENERATED_CONTENT_001": f"AI generation signals detected: {', '.join(matched_keywords[:3])}",
        }
        return observations.get(rule_id, f"Signal detected in {category} category.")
    
    def _generate_significance(self, category: str) -> str:
        """Generate explanation of why this signal matters to users."""
        significance_map = {
            "AI Use & Disclosure": "Knowing when AI is used helps you understand how content was created or delivered.",
            "Transparency": "Understanding how AI systems work helps you evaluate whether you agree with their decisions.",
            "Privacy & Data Use": "Clear data practices help you make informed decisions about sharing personal information.",
            "Fairness & Bias": "Awareness of bias testing helps you understand if AI systems might have disparate impacts.",
            "Human Oversight & Accountability": "Knowing humans review decisions and appeals exist helps ensure accountability for AI mistakes.",
            "Manipulation & Deceptive Practices": "Understanding personalization and targeting helps protect you from manipulation.",
            "Evidence & Claims": "Supporting evidence and methodology help you evaluate AI-driven claims and predictions.",
            "AI-Generated Content Signals": "Knowing content is AI-generated helps you evaluate its trustworthiness and context.",
        }
        return significance_map.get(
            category,
            "This signal relates to responsible AI practices.",
        )


def create_detector() -> ResponsibleAIDetector:
    """Factory function to create and initialize detector."""
    return ResponsibleAIDetector()
