"""Mamoru backend — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

from backend.schemas import ExtractionRequest, AnalysisResponse, ResponsibleAIAnalysisResult
from backend.rules import create_detector

app = FastAPI(
    title="Mamoru",
    description="Privacy-first, user-initiated browser safety assistant.",
    version="0.1.0",
)

# The popup runs as a chrome-extension:// page, so the browser may send CORS
# checks when it talks to this local API. This allows those local requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize responsible AI detector (M6)
detector = create_detector()


@app.get("/")
def root() -> dict[str, str]:
    """Simple confirmation that the application process is running."""
    return {
        "name": "Mamoru",
        "japanese_name": "マモル",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Confirm that Mamoru's backend is running."""
    return {
        "status": "ok",
        "service": "mamoru-backend",
        "message": "Mamoru backend is running.",
    }


@app.post("/analyze")
def analyze(request: ExtractionRequest) -> ResponsibleAIAnalysisResult:
    """
    M5+M6: Accept extracted webpage content and analyze for responsible AI signals.
    
    Privacy:
    - Content is processed in memory only
    - Content is NOT stored to disk or database
    - Only minimal metadata may be logged (URL, timestamp, word count)
    - Full content is ephemeral and discarded after processing
    
    M6: Responsible AI Signal Detection
    - Uses pattern-based rules to detect AI transparency, privacy, fairness signals
    - No LLM calls
    - No judgment verdicts ("safe/unsafe")
    - Returns findings with evidence and confidence (HIGH/MEDIUM/LOW only)
    
    Args:
        request: ExtractionRequest containing URL, title, content, etc.
    
    Returns:
        ResponsibleAIAnalysisResult with responsible AI signals detected
    """
    # Start timer for execution metric
    start_time = time.time()
    
    # Generate unique ID for this analysis
    analysis_id = str(uuid.uuid4())
    
    try:
        # M6: Run responsible AI detector
        signals = detector.analyze(
            content=request.content,
            url=request.url,
            title=request.title,
        )
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        return ResponsibleAIAnalysisResult(
            status="ok",
            message="Responsible AI analysis complete",
            analysisId=analysis_id,
            responsibleAISignals=signals,
            analysisMetadata={
                "categoriesAnalyzed": 8,
                "signalsDetected": len(signals),
                "analysisVersion": "1.0",
                "executionTimeMs": execution_time_ms,
            }
        )
    
    except Exception as e:
        # Return error response
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return ResponsibleAIAnalysisResult(
            status="error",
            message=f"Analysis error: {str(e)}",
            analysisId=analysis_id,
            responsibleAISignals=[],
            analysisMetadata={
                "error": str(e),
                "executionTimeMs": execution_time_ms,
            }
        )

