from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "AI MarketGuard"
    assert payload["backend"] == "available"
    assert payload["model"] in {"available", "unavailable"}
    assert payload["data"] in {"available", "unavailable"}
    assert payload["database"] in {"available", "unavailable"}
