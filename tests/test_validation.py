from fastapi.testclient import TestClient

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
    canary = "CANARY_OVERSIZE_" + ("x" * 100)
    huge = canary + ("y" * 50001)
    response = client.post(
        "/analyze",
        json=_body(content=huge, wordCount=1),
        headers=TOKEN_HEADER,
    )
    assert response.status_code in (413, 422)
    assert canary not in response.text


def test_missing_fields_generic_error():
    response = client.post("/analyze", json={"url": "https://x.example.test"}, headers=TOKEN_HEADER)
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid request. Check field types and sizes."
