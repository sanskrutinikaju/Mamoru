"""
Responsible AI Signal Detection Rules Package

Provides rule definitions and detection engine for identifying
responsible AI signals in webpage content.
"""

from .detector import ResponsibleAIDetector, create_detector

__all__ = [
    "ResponsibleAIDetector",
    "create_detector",
]
