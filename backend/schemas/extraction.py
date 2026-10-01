"""
Extraction and analysis schemas for Mamoru backend.

M5: Handles webpage content extraction and validation.
M6: Detects responsible AI signals in content.

Privacy: Content is accepted, processed, and NOT stored.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ExtractionRequest(BaseModel):
    """Request body for POST /analyze endpoint (M5)."""

    url: str = Field(..., description="URL of the page being analyzed")
    title: str = Field(..., description="Page title")
    language: str = Field(
        default="unknown", description="Detected language code (en, ja, etc.)"
    )
    wordCount: int = Field(..., description="Word count of extracted content")
    content: str = Field(..., description="Extracted visible page content")
    consentTimestamp: str = Field(
        ..., description="ISO timestamp of user's explicit click"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "title": "Example Article",
                "language": "en",
                "wordCount": 1250,
                "content": "This is the visible text content...",
                "consentTimestamp": "2026-10-01T14:30:00Z",
            }
        }


class ResponsibleAISignal(BaseModel):
    """A single responsible AI signal detected in content (M6)."""

    signalId: str = Field(
        description="Unique identifier for this signal rule"
    )
    category: str = Field(
        description="One of 8 responsible AI categories"
    )
    confidence: str = Field(
        description="Confidence level: HIGH, MEDIUM, or LOW (never probability)"
    )
    evidence: str = Field(
        description="What was found in the content (factual)"
    )
    observation: str = Field(
        description="Factual statement of what was observed"
    )
    interpretation: str = Field(
        description="Why this matters for responsible AI"
    )
    falsePossibilities: str = Field(
        description="How this signal could be incorrect or misleading"
    )
    significance: str = Field(
        description="Why users should care about this signal"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "signalId": "TRANSPARENCY_001",
                "category": "Transparency",
                "confidence": "HIGH",
                "evidence": "Found detailed algorithm explanation in 'How it works' section",
                "observation": "Page explicitly explains how recommendation algorithm selects content",
                "interpretation": "High transparency about AI decision-making",
                "falsePossibilities": "Page may oversimplify or misrepresent actual algorithm behavior",
                "significance": "Transparency helps users understand why content appears"
            }
        }


class AnalysisResponse(BaseModel):
    """Response body for POST /analyze endpoint (M5 stub)."""

    status: str = Field(description="Analysis status: ok or error")
    message: str = Field(description="Response message to user")
    analysisId: str = Field(
        description="Unique ID for this analysis (for later retrieval)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "Mamoru analysis complete.",
                "analysisId": "550e8400-e29b-41d4-a716-446655440000",
            }
        }


class ResponsibleAIAnalysisResult(BaseModel):
    """Response body for POST /analyze endpoint (M6 - with responsible AI signals)."""

    status: str = Field(
        description="Analysis status: ok or error"
    )
    message: str = Field(
        description="Response message to user"
    )
    analysisId: str = Field(
        description="Unique ID for this analysis (for later retrieval)"
    )
    responsibleAISignals: List[ResponsibleAISignal] = Field(
        default=[],
        description="List of responsible AI signals detected (HIGH/MEDIUM/LOW confidence)"
    )
    analysisMetadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about the analysis (categories analyzed, signals detected, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "Responsible AI analysis complete",
                "analysisId": "550e8400-e29b-41d4-a716-446655440000",
                "responsibleAISignals": [
                    {
                        "signalId": "TRANSPARENCY_001",
                        "category": "Transparency",
                        "confidence": "HIGH",
                        "evidence": "Found detailed algorithm explanation in 'How it works' section",
                        "observation": "Page explicitly explains how recommendation algorithm selects content",
                        "interpretation": "High transparency about AI decision-making",
                        "falsePossibilities": "Page may oversimplify or misrepresent actual algorithm",
                        "significance": "Transparency helps users understand why content appears"
                    }
                ],
                "analysisMetadata": {
                    "categoriesAnalyzed": 8,
                    "signalsDetected": 1,
                    "analysisVersion": "1.0",
                    "executionTimeMs": 125
                }
            }
        }

