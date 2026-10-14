from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from application import app
from constants.application_constants import CLIENT_KEY_HEADER
from services import channel_service, health_service, youtube_client_service

client = TestClient(app)
AUTH_HEADERS = {CLIENT_KEY_HEADER: "test-client-key"}


@pytest.fixture(autouse=True)
def _mock_db_health(monkeypatch):
    async def fake_healthy() -> bool:
        return True

    monkeypatch.setattr(health_service, "is_database_healthy", fake_healthy)


def test_parse_channel_input_formats():
    assert channel_service.parse_channel_input("UC_x5XG1OV2P6uZZ5FSM9Ttw") == (
        "id",
        "UC_x5XG1OV2P6uZZ5FSM9Ttw",
    )
    assert channel_service.parse_channel_input(
        "https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw"
    ) == ("id", "UC_x5XG1OV2P6uZZ5FSM9Ttw")
    assert channel_service.parse_channel_input("@mkbhd") == ("handle", "mkbhd")
    assert channel_service.parse_channel_input("https://youtube.com/@mkbhd") == ("handle", "mkbhd")
    assert channel_service.parse_channel_input("https://www.youtube.com/user/pewdiepie") == (
        "username",
        "pewdiepie",
    )
    assert channel_service.parse_channel_input("https://www.youtube.com/c/creatorname") == (
        "legacy_c",
        "creatorname",
    )

    with pytest.raises(ValueError, match="empty"):
        channel_service.parse_channel_input("   ")


def test_parse_keywords():
    raw = 'tech "smart phones" reviews gadgets'
    assert channel_service.parse_keywords(raw) == ["tech", "smart phones", "reviews", "gadgets"]
    assert channel_service.parse_keywords("") == []
    assert channel_service.parse_keywords(None) == []


@pytest.mark.anyio
async def test_resolve_legacy_c_warning_without_confirm():
    with pytest.raises(channel_service.LegacyCustomUrlWarning, match="100 quota units"):
        await channel_service.resolve_channel_input(
            "https://www.youtube.com/c/oldchannel", confirm_legacy=False
        )


@pytest.mark.anyio
async def test_resolve_legacy_c_with_confirm(monkeypatch):
    # Mock search call (100 units) and channels call (1 unit)
    search_return = {
        "items": [{"id": {"channelId": "UC1234567890123456789012"}}]
    }
    channels_return = {
        "items": [
            {
                "id": "UC1234567890123456789012",
                "snippet": {
                    "title": "Legacy Creator",
                    "description": "A channel",
                    "customUrl": "@legacy",
                    "country": "US",
                    "publishedAt": "2015-01-01T00:00:00Z",
                },
                "statistics": {
                    "subscriberCount": "500000",
                    "viewCount": "10000000",
                    "videoCount": "250",
                    "hiddenSubscriberCount": False,
                },
                "contentDetails": {"relatedPlaylists": {"uploads": "UU1234567890123456789012"}},
                "brandingSettings": {"channel": {"keywords": "legacy test"}},
                "topicDetails": {"topicCategories": []},
            }
        ]
    }

    async def fake_search(*args, **kwargs):
        return search_return

    async def fake_channels(*args, **kwargs):
        return channels_return

    monkeypatch.setattr(youtube_client_service, "fetch_search", fake_search)
    monkeypatch.setattr(youtube_client_service, "fetch_channels", fake_channels)

    # Mock DB save
    async def fake_save(data):
        from unittest.mock import MagicMock
        obj = MagicMock()
        for k, v in data.items():
            setattr(obj, k, v)
        obj.tracked = False
        obj.createdAt = datetime.now(UTC)
        obj.updatedAt = datetime.now(UTC)
        return obj

    monkeypatch.setattr(channel_service, "_save_channel_to_db", fake_save)

    async def fake_find_unique(channel_id):
        return None

    monkeypatch.setattr(channel_service, "_find_cached_channel", fake_find_unique)

    channel, quota_spent, cached = await channel_service.resolve_channel_input(
        "https://www.youtube.com/c/legacycreator", confirm_legacy=True
    )
    assert quota_spent == 101
    assert cached is False
    assert channel.id == "UC1234567890123456789012"
    assert channel.subscriberCount == 500000
    assert channel.subscriberCountHidden is False


@pytest.mark.anyio
async def test_hidden_subscriber_count_stored_as_none():
    item = {
        "id": "UC_hidden_subscribers_1234",
        "snippet": {"title": "Hidden Subs Channel"},
        "statistics": {
            "subscriberCount": "0",
            "hiddenSubscriberCount": True,
            "viewCount": "5000",
            "videoCount": "10",
        },
        "contentDetails": {},
        "brandingSettings": {},
        "topicDetails": {},
    }
    parsed = channel_service._parse_channel_resource(item)
    # Per R-8: hidden subscriber count must be stored as None, never 0
    assert parsed["subscriberCount"] is None
    assert parsed["subscriberCountHidden"] is True


def test_post_channels_resolve_endpoint(monkeypatch):
    # Unauthenticated
    assert client.post("/channels/resolve", json={"input": "@mkbhd"}).status_code == 401

    # Legacy URL without confirm
    res_warn = client.post(
        "/channels/resolve",
        headers=AUTH_HEADERS,
        json={"input": "https://www.youtube.com/c/testchannel", "confirm_legacy": False},
    )
    assert res_warn.status_code == 400
    assert "100 quota units" in res_warn.json()["detail"]

    # Valid resolution mock
    async def fake_resolve(input_str, refresh=False, confirm_legacy=False):
        from unittest.mock import MagicMock
        obj = MagicMock()
        obj.id = "UC_x5XG1OV2P6uZZ5FSM9Ttw"
        obj.title = "Marques Brownlee"
        obj.description = "Quality tech videos"
        obj.customUrl = "@mkbhd"
        obj.country = "US"
        obj.publishedAt = datetime(2008, 3, 21, tzinfo=UTC)
        obj.subscriberCount = 18000000
        obj.subscriberCountHidden = False
        obj.viewCount = 4000000000
        obj.videoCount = 1600
        obj.keywords = ["tech", "mkbhd"]
        obj.topicCategories = []
        obj.uploadsPlaylistId = "UU_x5XG1OV2P6uZZ5FSM9Ttw"
        obj.tracked = False
        obj.fetchedAt = datetime.now(UTC)
        obj.createdAt = datetime.now(UTC)
        obj.updatedAt = datetime.now(UTC)
        return obj, 1, False

    monkeypatch.setattr(channel_service, "resolve_channel_input", fake_resolve)

    response = client.post(
        "/channels/resolve",
        headers=AUTH_HEADERS,
        json={"input": "@mkbhd"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quota_spent"] == 1
    assert data["cached"] is False
    assert data["resolved_id"] == "UC_x5XG1OV2P6uZZ5FSM9Ttw"
    assert data["channel"]["title"] == "Marques Brownlee"
    assert data["channel"]["subscriber_count"] == 18000000
