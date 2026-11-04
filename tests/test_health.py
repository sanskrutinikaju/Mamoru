from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "mamoru-backend"


def test_root_ok():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Mamoru"
