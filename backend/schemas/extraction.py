"""Request and response shapes for POST /analyze.

Content is accepted in memory, validated, and not stored.
This milestone only acknowledges the request. It does not run a rule engine or LLM.
"""

from pydantic import BaseModel, Field

from backend.config import DEFAULT_MAX_CONTENT_CHARS


class ExtractionRequest(BaseModel):
    """Body sent by the extension after the user confirms extraction."""

    url: str = Field(min_length=1, max_length=2048)
    title: str = Field(min_length=1, max_length=512)
    language: str = Field(default="unknown", max_length=16)
    wordCount: int = Field(ge=0, le=2_000_000)
    content: str = Field(min_length=0, max_length=DEFAULT_MAX_CONTENT_CHARS)
    consentTimestamp: str = Field(min_length=1, max_length=64)


class AnalysisResponse(BaseModel):
    """Acknowledgement that the backend received a valid, authorized request."""

    status: str
    message: str
    analysisId: str
