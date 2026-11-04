"""Webpage content must never appear in logs or error JSON."""

import logging

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
TOKEN_HEADER = {"X-Mamoru-Token": "test-token-ci"}

# Unique marker used only in tests. Not taken from a real webpage.
CANARY = "CANARY_MAMORU_LOG_TEST_9f3a7c21e4b0"


def test_analyze_success_does_not_log_page_content(caplog):
    caplog.set_level(logging.DEBUG)
    body = {
        "url": "https://safe.example.test/page",
        "title": "Example page",
        "language": "en",
        "wordCount": 1,
        "content": CANARY,
        "consentTimestamp": "2026-11-04T00:00:00Z",
    }
    response = client.post("/analyze", json=body, headers=TOKEN_HEADER)
    assert response.status_code == 200
    assert CANARY not in caplog.text
    assert CANARY not in response.text


def test_validation_error_does_not_echo_page_content():
    body = {
        "url": "https://safe.example.test/page",
        "title": "Example page",
        "language": "en",
        "wordCount": "not-a-number",
        "content": CANARY,
        "consentTimestamp": "2026-11-04T00:00:00Z",
    }
    response = client.post("/analyze", json=body, headers=TOKEN_HEADER)
    assert response.status_code == 422
    assert CANARY not in response.text
