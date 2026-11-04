"""A request without the shared token must be rejected."""

from fastapi.testclient import TestClient

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
