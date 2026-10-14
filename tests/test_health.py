import pytest
from fastapi.testclient import TestClient

from application import app
from services import health_service

# No `with TestClient(...)`: the lifespan (database connect) is skipped and the DB check is stubbed.
client = TestClient(app)


@pytest.mark.parametrize(("healthy", "status_code", "state"), [(True, 200, "ok"), (False, 503, "error")])
def test_health_reports_database_state(monkeypatch, healthy, status_code, state):
    async def fake_check() -> bool:
        return healthy

    monkeypatch.setattr(health_service, "is_database_healthy", fake_check)

    response = client.get("/health")

    assert response.status_code == status_code
    assert response.json() == {"status": state, "database": state}


def test_home_page_is_public_html():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "/api-docs" in response.text


def test_docs_are_public():
    assert client.get("/api-docs").status_code == 200
    assert client.get("/api-docs/openapi.json").status_code == 200
