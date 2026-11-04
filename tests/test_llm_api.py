from fastapi.testclient import TestClient

from backend.llm.service import LLMService
from backend.main import app
from backend.schemas.analysis import LLMAnalysis

client = TestClient(app)
TOKEN_HEADER = {"X-Mamoru-Token": "test-token-ci"}


class FakeProvider:
    def __init__(self):
        self.received_text = None

    def analyze(self, _page_text):
        self.received_text = _page_text
        return LLMAnalysis(
            findings=[
                {
                    "category": "credential_request",
                    "severity": "Low",
                    "evidence": "enter your account password",
                    "explanation": "The text asks the reader for a password.",
                }
            ]
        )


def test_analyze_returns_rule_floor_and_llm_findings(monkeypatch):
    provider = FakeProvider()
    monkeypatch.setattr("backend.main.llm_service", LLMService(provider))
    body = {
        "url": "https://sample.example.test/login",
        "title": "Synthetic login page",
        "language": "en",
        "wordCount": 6,
        "content": "Please enter your account password to continue.",
        "consentTimestamp": "2026-11-04T00:00:00Z",
    }

    response = client.post("/analyze", json=body, headers=TOKEN_HEADER)

    assert response.status_code == 200
    result = response.json()
    assert result["llmStatus"] == "completed"
    assert result["findings"][0]["severity"] == "High"
    assert result["llmFindings"][0]["severity"] == "High"
    assert result["llmFindings"][0]["evidence"] == "enter your account password"
    assert provider.received_text == body["content"]
    assert body["url"] not in provider.received_text
    assert body["title"] not in provider.received_text
    assert result["safetyReport"]["overallLevel"] == "High"
    assert len(result["safetyReport"]["findings"]) == 1
    assert result["safetyReport"]["findings"][0]["confidence"] == "High"
