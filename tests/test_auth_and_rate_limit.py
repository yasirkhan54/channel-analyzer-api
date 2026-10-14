import pytest
from fastapi.testclient import TestClient

from application import app
from configurations.environment_configuration import get_settings
from constants.application_constants import CLIENT_KEY_HEADER
from middleware.rate_limit_middleware import reset_rate_limits
from services import health_service, quota_service

client = TestClient(app)
AUTH_HEADERS = {CLIENT_KEY_HEADER: "test-client-key"}


@pytest.fixture(autouse=True)
def _mock_db_and_clear_rate_limits(monkeypatch):
    reset_rate_limits()

    async def fake_healthy() -> bool:
        return True

    async def fake_quota_status() -> dict[str, object]:
        return {
            "units_used": 0,
            "units_remaining": 10000,
            "safety_margin": 200,
            "daily_limit": 10000,
            "next_reset_pacific": "2026-10-06T00:00:00-07:00",
            "next_reset_pkt": "2026-10-06T12:00:00+05:00",
            "next_reset_utc": "2026-10-06T07:00:00+00:00",
            "used": 0,
            "remaining": 10000,
            "margin": 200,
        }

    monkeypatch.setattr(health_service, "is_database_healthy", fake_healthy)
    monkeypatch.setattr(quota_service, "get_quota_status", fake_quota_status)
    yield
    reset_rate_limits()


def test_openapi_schema_security_and_authorize():
    response = client.get("/api-docs/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    # Security schemes for Swagger Authorize button
    components = schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    assert "APIKeyHeader" in security_schemes
    auth_config = security_schemes["APIKeyHeader"]
    assert auth_config["type"] == "apiKey"
    assert auth_config["in"] == "header"
    assert auth_config["name"] == CLIENT_KEY_HEADER

    # Every scheme an endpoint requires must be defined, or Swagger UI sends no key header
    used = {
        name
        for operations in schema["paths"].values()
        for operation in operations.values()
        for requirement in operation.get("security", [])
        for name in requirement
    }
    assert used == {"APIKeyHeader"}
    assert used <= set(security_schemes)

    # All paths exist in OpenAPI JSON
    paths = schema.get("paths", {})
    assert "/health" in paths
    assert "/quota" in paths


def test_client_key_authentication():
    # Public paths do not require key
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200

    # Protected paths require client key
    assert client.get("/quota").status_code == 401
    assert client.get("/quota", headers={CLIENT_KEY_HEADER: "invalid-key"}).status_code == 401
    assert client.get("/quota", headers=AUTH_HEADERS).status_code == 200


def test_rate_limiting_enforcement(monkeypatch):
    # Temporarily set small limit for testing
    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_requests", 3)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)

    # 3 allowed
    for _ in range(3):
        res = client.get("/quota", headers=AUTH_HEADERS)
        assert res.status_code == 200

    # 4th request should be rate-limited (429)
    res_limited = client.get("/quota", headers=AUTH_HEADERS)
    assert res_limited.status_code == 429
    assert res_limited.json() == {"detail": "Rate limit exceeded. Too many requests."}
    assert "Retry-After" in res_limited.headers


def test_rate_limiting_skips_public_paths(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_requests", 2)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)

    # Public paths should not trigger 429 even past the limit
    for _ in range(5):
        assert client.get("/health").status_code == 200
