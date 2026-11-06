import json

import pytest
from fastapi.testclient import TestClient

from backend.config import (
    get_gemini_max_calls_per_run,
    get_gemini_min_seconds_between_calls,
    get_gemini_model,
    get_max_content_chars,
)
from backend.main import app

client = TestClient(app)
TOKEN_HEADER = {"X-Mamoru-Token": "test-token-ci"}


def _body(**overrides):
    data = {
        "url": "https://news.example.test/article",
        "title": "Example article",
        "language": "en",
        "wordCount": 3,
        "content": "Just an example.",
        "consentTimestamp": "2026-11-04T00:00:00Z",
    }
    data.update(overrides)
    return data


def test_oversize_content_is_rejected_without_echoing_it():
    canary = "SYNTHETIC_OVERSIZE_MARKER"
    huge = canary + ("x" * 400000)
    response = client.post(
        "/analyze",
        json=_body(content=huge, wordCount=1),
        headers=TOKEN_HEADER,
    )
    assert response.status_code == 413
    assert canary not in response.text


def test_oversize_stream_without_content_length_is_rejected():
    body = _body(content="x" * 400000, wordCount=1)
    encoded_body = json.dumps(body).encode("utf-8")
    response = client.post(
        "/analyze",
        content=iter((encoded_body,)),
        headers={
            **TOKEN_HEADER,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "Request is too large."


def test_missing_fields_generic_error():
    response = client.post("/analyze", json={"url": "https://x.example.test"}, headers=TOKEN_HEADER)
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid request. Check field types and sizes."


def test_invalid_content_limit_is_reported(monkeypatch):
    monkeypatch.setenv("MAMORU_MAX_CONTENT_CHARS", "not-a-number")
    with pytest.raises(ValueError, match="positive integer"):
        get_max_content_chars()


def test_gemini_model_is_required_and_validated(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    with pytest.raises(ValueError, match="GEMINI_MODEL is required"):
        get_gemini_model()

    monkeypatch.setenv("GEMINI_MODEL", "not-a-gemini-model")
    with pytest.raises(ValueError, match="valid Gemini model ID"):
        get_gemini_model()

    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    assert get_gemini_model() == "gemini-2.5-flash"


def test_gemini_run_controls_default_and_validate(monkeypatch):
    monkeypatch.delenv("GEMINI_MIN_SECONDS_BETWEEN_CALLS", raising=False)
    monkeypatch.delenv("GEMINI_MAX_CALLS_PER_RUN", raising=False)
    assert get_gemini_min_seconds_between_calls() == 12.0
    assert get_gemini_max_calls_per_run() == 40

    monkeypatch.setenv("GEMINI_MIN_SECONDS_BETWEEN_CALLS", "0")
    monkeypatch.setenv("GEMINI_MAX_CALLS_PER_RUN", "1")
    assert get_gemini_min_seconds_between_calls() == 0.0
    assert get_gemini_max_calls_per_run() == 1

    monkeypatch.setenv("GEMINI_MIN_SECONDS_BETWEEN_CALLS", "nan")
    with pytest.raises(ValueError, match="finite non-negative number"):
        get_gemini_min_seconds_between_calls()
    monkeypatch.setenv("GEMINI_MAX_CALLS_PER_RUN", "0")
    with pytest.raises(ValueError, match="positive integer"):
        get_gemini_max_calls_per_run()
