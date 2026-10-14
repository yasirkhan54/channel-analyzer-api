from datetime import date, datetime
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import httpx
import pytest
from fastapi.testclient import TestClient

from application import app
from services import quota_service, youtube_client_service

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-client-key"}


def test_pacific_time_and_reset_calculations():
    pacific_date = quota_service.get_current_pacific_date()
    assert isinstance(pacific_date, date)

    fixed_now = datetime(2026, 10, 2, 14, 30, tzinfo=ZoneInfo("America/Los_Angeles"))
    reset_pacific, reset_pkt, reset_utc = quota_service.get_next_reset_times(fixed_now)

    # Next midnight in Pacific time: 2026-10-03 00:00:00-07:00 (PDT)
    assert reset_pacific.isoformat() == "2026-10-03T00:00:00-07:00"
    # In PKT (UTC+5): 07:00 UTC + 5h = 12:00 PKT (R-2)
    assert reset_pkt.isoformat() == "2026-10-03T12:00:00+05:00"
    assert reset_utc.isoformat() == "2026-10-03T07:00:00+00:00"


@pytest.mark.anyio
async def test_quota_service_usage_and_safety_margin(monkeypatch):
    # Mock database calls for pure unit testing
    current_spent = 0

    async def fake_get_quota_usage(quota_day=None, google_project_id="default"):
        return current_spent

    monkeypatch.setattr(quota_service, "get_quota_usage", fake_get_quota_usage)

    # Limit = 10000, margin = 200 => max usable = 9800
    current_spent = 9799
    assert await quota_service.check_quota_available(cost=1) is True
    assert await quota_service.check_quota_available(cost=2) is False

    current_spent = 9800
    assert await quota_service.check_quota_available(cost=1) is False


@pytest.mark.anyio
async def test_youtube_client_safety_margin_refusal(monkeypatch):
    async def fake_check(cost=1, google_project_id="default"):
        return False

    monkeypatch.setattr(quota_service, "check_quota_available", fake_check)

    with pytest.raises(youtube_client_service.QuotaExhaustedError, match="cuts into safety margin"):
        await youtube_client_service.call_api("videos", {"id": "test"}, unit_cost=1)


@pytest.mark.anyio
async def test_youtube_client_success_records_quota(monkeypatch):
    async def fake_check(cost=1, google_project_id="default"):
        return True

    recorded = []

    async def fake_record(cost, quota_day=None, google_project_id="default"):
        recorded.append(cost)
        return cost

    monkeypatch.setattr(quota_service, "check_quota_available", fake_check)
    monkeypatch.setattr(quota_service, "record_quota_spent", fake_record)

    fake_response = httpx.Response(200, json={"items": [{"id": "vid1"}]})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_response
        result = await youtube_client_service.call_api("videos", {"id": "vid1"}, unit_cost=1)

    assert result == {"items": [{"id": "vid1"}]}
    assert recorded == [1]


@pytest.mark.anyio
async def test_youtube_client_quota_exceeded_error(monkeypatch):
    async def fake_check(cost=1, google_project_id="default"):
        return True

    monkeypatch.setattr(quota_service, "check_quota_available", fake_check)

    error_payload = {
        "error": {
            "code": 403,
            "message": "The request cannot be completed because you have exceeded your quota.",
            "errors": [
                {
                    "message": "The request cannot be completed because you have exceeded your quota.",
                    "domain": "youtube.quota",
                    "reason": "quotaExceeded",
                }
            ],
        }
    }
    fake_response = httpx.Response(403, json=error_payload)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_response
        with pytest.raises(youtube_client_service.QuotaExhaustedError, match="quotaExceeded"):
            await youtube_client_service.call_api("videos", {"id": "vid1"}, unit_cost=1)


@pytest.mark.anyio
async def test_youtube_client_not_found_error(monkeypatch):
    async def fake_check(cost=1, google_project_id="default"):
        return True

    monkeypatch.setattr(quota_service, "check_quota_available", fake_check)
    fake_response = httpx.Response(404, text="Not Found")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_response
        with pytest.raises(youtube_client_service.ResourceNotFoundError, match="not found"):
            await youtube_client_service.call_api("channels", {"id": "unknown"}, unit_cost=1)


@pytest.mark.anyio
async def test_youtube_client_server_error(monkeypatch):
    async def fake_check(cost=1, google_project_id="default"):
        return True

    monkeypatch.setattr(quota_service, "check_quota_available", fake_check)
    fake_response = httpx.Response(503, text="Service Unavailable")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_response
        with pytest.raises(youtube_client_service.YouTubeServerError, match="503"):
            await youtube_client_service.call_api("channels", {"id": "test"}, unit_cost=1)


def test_get_quota_endpoint(monkeypatch):
    # Unauthenticated
    assert client.get("/quota").status_code == 401

    # Authenticated
    async def fake_get_status():
        return {
            "units_used": 150,
            "units_remaining": 9850,
            "safety_margin": 200,
            "daily_limit": 10000,
            "next_reset_pacific": "2026-10-03T00:00:00-07:00",
            "next_reset_pkt": "2026-10-03T12:00:00+05:00",
            "next_reset_utc": "2026-10-03T07:00:00Z",
            "used": 150,
            "remaining": 9850,
            "margin": 200,
        }

    monkeypatch.setattr(quota_service, "get_quota_status", fake_get_status)

    response = client.get("/quota", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["units_used"] == 150
    assert data["units_remaining"] == 9850
    assert data["safety_margin"] == 200
    assert data["daily_limit"] == 10000
    assert "next_reset_pacific" in data
    assert "next_reset_pkt" in data
    assert data["used"] == 150
    assert data["remaining"] == 9850
