"""
Confidence scoring logic for Responsible AI signals.

Confidence levels: HIGH, MEDIUM, LOW (never probability scores)
"""

from typing import List
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def calculate_keyword_confidence(
    text: str,
    keywords: List[str],
    min_matches: int = 1,
) -> ConfidenceLevel:
    """
    Calculate confidence based on keyword matches.
    
    Args:
        text: Content to search
        keywords: List of keywords to match (case-insensitive)
        min_matches: Minimum keywords found to register a match
    
    Returns:
        ConfidenceLevel based on keyword density and count
    """
    text_lower = text.lower()
    
    # Count keyword matches
    matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    if matches == 0:
        return None  # No signal detected
    
    # Confidence based on number of matches and min_matches threshold
    if matches >= min_matches * 3:
        return ConfidenceLevel.HIGH
    elif matches >= min_matches * 1.5:
        return ConfidenceLevel.MEDIUM
    elif matches >= min_matches:
        return ConfidenceLevel.LOW
    
    return None


def calculate_combined_confidence(
    signals: List[tuple],  # List of (signal_type, confidence) tuples
) -> ConfidenceLevel:
    """
    Combine multiple signals to determine overall confidence for a category.
    
    Args:
        signals: List of (signal_name, confidence_level) tuples
    
    Returns:
        Combined ConfidenceLevel
    """
    if not signals:
        return None
    
    highs = sum(1 for _, conf in signals if conf == ConfidenceLevel.HIGH)
    mediums = sum(1 for _, conf in signals if conf == ConfidenceLevel.MEDIUM)
    
    # If multiple high signals, overall is HIGH
    if highs >= 1:
        return ConfidenceLevel.HIGH
    # If multiple medium signals, overall is MEDIUM
    elif mediums >= 2:
        return ConfidenceLevel.MEDIUM
    # Single medium signal is MEDIUM
    elif mediums >= 1:
        return ConfidenceLevel.MEDIUM
    # Otherwise LOW
    else:
        return ConfidenceLevel.LOW


def describe_confidence_limitation(confidence: ConfidenceLevel) -> str:
    """
    Return a disclaimer about confidence level limitations.
    """
    if confidence == ConfidenceLevel.HIGH:
        return "High confidence indicates strong evidence but does not provide absolute certainty."
    elif confidence == ConfidenceLevel.MEDIUM:
        return "Medium confidence indicates potential signal but may indicate false positive."
    else:
        return "Low confidence indicates weak or ambiguous signal; interpretation required."
