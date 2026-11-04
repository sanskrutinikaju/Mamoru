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
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.config import (
    get_api_token,
    get_extension_origin,
    get_max_content_chars,
)
from backend.llm.service import create_llm_service
from backend.reporting import build_safety_report
from backend.rules import RuleEngine
from backend.schemas import AnalysisResponse, ExtractionRequest, RuleFinding

logger = logging.getLogger("mamoru")
rule_engine = RuleEngine()
llm_service = create_llm_service()


def get_max_request_bytes() -> int:
    """Allow for JSON escaping and request metadata around the page text."""
    return get_max_content_chars() * 6 + 8192


class RequestSizeLimitMiddleware:
    """Reject oversized requests, including bodies without Content-Length."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        max_bytes = get_max_request_bytes()
        headers = {name.lower(): value for name, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                await JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header."},
                )(scope, receive, send)
                return
            if declared_length < 0:
                await JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header."},
                )(scope, receive, send)
                return
            if declared_length > max_bytes:
                await JSONResponse(
                    status_code=413,
                    content={"detail": "Request is too large."},
                )(scope, receive, send)
                return

        messages: list[Message] = []
        total_bytes = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                messages.append(message)
                break

            total_bytes += len(message.get("body", b""))
            if total_bytes > max_bytes:
                await JSONResponse(
                    status_code=413,
                    content={"detail": "Request is too large."},
                )(scope, receive, send)
                return

            messages.append(message)
            if not message.get("more_body", False):
                break

        replay_index = 0

        async def replay_request_body() -> Message:
            nonlocal replay_index
            if replay_index < len(messages):
                message = messages[replay_index]
                replay_index += 1
                return message
            return {"type": "http.disconnect"}

        await self.app(scope, replay_request_body, send)


app = FastAPI(
    title="Mamoru",
    description="Consent-first, user-initiated browser threat analyzer.",
    version="0.1.0",
)

extension_origin = get_extension_origin()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[extension_origin] if extension_origin else [],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Mamoru-Token"],
)
app.add_middleware(RequestSizeLimitMiddleware)


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
    """Log request metadata only; never read or log the request body."""
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
    """Analyze consented text without storing or logging the page content."""
    findings = rule_engine.analyze(request.content)
    llm_result = llm_service.analyze(request.content, findings)
    return AnalysisResponse(
        status="ok",
        message=(
            "Analysis completed. Findings are signals to review, not proof of harm."
        ),
        analysisId=str(uuid.uuid4()),
        findings=[
            RuleFinding(
                ruleId=finding.rule_id,
                description=finding.description,
                severity=finding.severity,
                category=finding.category,
                evidence=finding.evidence,
            )
            for finding in findings
        ],
        llmStatus=llm_result.status,
        llmMessage=llm_result.message,
        llmFindings=llm_result.findings,
        safetyReport=build_safety_report(findings, llm_result.findings),
    )
