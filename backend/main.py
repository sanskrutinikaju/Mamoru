"""Mamoru backend — local FastAPI app.

Webpage text is treated as untrusted data. It is never stored and never
written into logs or error messages.
"""

import logging
import secrets
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_api_token, get_max_content_chars
from backend.schemas import AnalysisResponse, ExtractionRequest

logger = logging.getLogger("mamoru")

app = FastAPI(
    title="Mamoru",
    description="Consent-first, user-initiated browser threat analyzer.",
    version="0.1.0",
)

# Only Chromium extension pages may call this API from a browser.
# Other websites fail the CORS preflight, so they cannot POST JSON here.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^chrome-extension://[a-p]{32}$",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Mamoru-Token"],
)


def require_token(x_mamoru_token: str | None = Header(default=None)) -> None:
    """Reject requests that do not present the shared secret."""
    expected = get_api_token()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Mamoru API token is not configured on the server.",
        )
    if x_mamoru_token is None or not secrets.compare_digest(
        x_mamoru_token, expected
    ):
        raise HTTPException(status_code=401, detail="Unauthorized.")


@app.middleware("http")
async def reject_huge_requests(request: Request, call_next):
    """Block oversized bodies using Content-Length. Do not read or log the body."""
    max_bytes = get_max_content_chars() * 4 + 8192
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            length = int(content_length)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length header."},
            )
        if length > max_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request is too large."},
            )

    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("status %s", response.status_code)
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a generic 422. Do not echo the submitted webpage text."""
    del request, exc
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request. Check field types and sizes."},
    )


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
    """Confirm that Mamoru's backend is running. No token required."""
    return {
        "status": "ok",
        "service": "mamoru-backend",
        "message": "Mamoru backend is running.",
    }


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(
    request: ExtractionRequest,
    _: None = Depends(require_token),
) -> AnalysisResponse:
    """Accept extracted text after user consent. Do not store it. Do not log it."""
    del request
    return AnalysisResponse(
        status="ok",
        message="Mamoru received the page text. Analysis features are not enabled yet.",
        analysisId=str(uuid.uuid4()),
    )
