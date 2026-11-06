"""A request without the shared token must be rejected."""

import pytest
from fastapi.testclient import TestClient

from backend.config import get_extension_origin
from backend.main import app

client = TestClient(app)

VALID_BODY = {
    "url": "https://shop.example.test/login",
    "title": "Example shop login",
    "language": "en",
    "wordCount": 4,
    "content": "Please sign in to continue.",
    "consentTimestamp": "2026-11-04T00:00:00Z",
}

TOKEN_HEADER = {"X-Mamoru-Token": "test-token-ci"}


def test_analyze_without_token_is_rejected():
    response = client.post("/analyze", json=VALID_BODY)
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized."


@pytest.mark.parametrize("server_token", ["", "   "])
def test_analyze_fails_closed_when_server_token_is_empty(monkeypatch, server_token):
    monkeypatch.setenv("MAMORU_API_TOKEN", server_token)

    response = client.post("/analyze", json=VALID_BODY, headers=TOKEN_HEADER)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Mamoru API token is not configured on the server."
    )


def test_analyze_with_wrong_token_is_rejected():
    response = client.post(
        "/analyze",
        json=VALID_BODY,
        headers={"X-Mamoru-Token": "wrong-token"},
    )
    assert response.status_code == 401


def test_analyze_with_token_is_accepted():
    response = client.post("/analyze", json=VALID_BODY, headers=TOKEN_HEADER)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "analysisId" in body
    assert body["findings"] == []
    assert body["llmStatus"] == "unavailable"
    assert body["llmFindings"] == []
    assert "disabled for live page text" in body["llmMessage"]
    assert body["safetyReport"]["overallLevel"] == "Cannot tell"
    assert body["safetyReport"]["findings"] == []


def test_analyze_returns_deterministic_rule_evidence():
    body = {
        **VALID_BODY,
        "content": "Please enter your account password to continue.",
    }
    response = client.post("/analyze", json=body, headers=TOKEN_HEADER)

    assert response.status_code == 200
    finding = response.json()["findings"][0]
    assert finding == {
        "ruleId": "credential_request",
        "description": "Requests a password, passcode, credentials, or verification code.",
        "severity": "High",
        "category": "credential_request",
        "evidence": "enter your account password",
    }
    assert response.json()["safetyReport"]["overallLevel"] == "High"


def test_cors_allows_only_the_configured_extension_origin():
    allowed_origin = "chrome-extension://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    response = client.options(
        "/analyze",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-mamoru-token",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == allowed_origin


def test_cors_rejects_other_extension_origins():
    response = client.options(
        "/analyze",
        headers={
            "Origin": "chrome-extension://bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-mamoru-token",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_invalid_extension_origin_is_rejected(monkeypatch):
    monkeypatch.setenv("MAMORU_EXTENSION_ORIGIN", "https://example.test")
    with pytest.raises(ValueError, match="32-character extension ID"):
        get_extension_origin()
