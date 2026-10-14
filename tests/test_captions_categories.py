from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from application import app
from services import (
    youtube_caption_service,
    youtube_category_service,
    youtube_client_service,
    youtube_video_service,
)
from services.youtube_client_service import ResourceNotFoundError

client = TestClient(app)
HEADERS = {"X-API-Key": "test-client-key"}


class FakeTransaction:
    def __init__(self, db):
        self.captiontrack = db.captiontrack

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


def fake_db(monkeypatch, module, video_count=1):
    db = MagicMock()
    db.video.count = AsyncMock(return_value=video_count)
    db.captiontrack.delete_many = AsyncMock()
    db.captiontrack.upsert = AsyncMock()
    db.captiontrack.find_many = AsyncMock(return_value=[])
    db.videocategory.upsert = AsyncMock()
    db.videocategory.find_many = AsyncMock(return_value=[])
    db.tx = lambda: FakeTransaction(db)
    monkeypatch.setattr(module, "database", db)
    return db


@pytest.mark.anyio
async def test_fetch_captions_stores_tracks_and_drops_removed_ones(monkeypatch):
    db = fake_db(monkeypatch, youtube_caption_service)
    items = [
        {"id": "c1", "snippet": {"language": "en", "trackKind": "standard", "isCC": True, "name": ""}},
        {
            "id": "c2",
            "snippet": {"language": "ur", "trackKind": "asr", "lastUpdated": "2026-01-02T03:04:05Z"},
        },
    ]
    monkeypatch.setattr(youtube_client_service, "fetch_captions", AsyncMock(return_value={"items": items}))
    fetch_video = AsyncMock()
    monkeypatch.setattr(youtube_video_service, "fetch_video", fetch_video)

    _, quota = await youtube_caption_service.fetch_video_captions("v1")

    assert quota == 50
    fetch_video.assert_not_called()  # the video is already stored
    db.captiontrack.delete_many.assert_awaited_once_with(
        where={"videoId": "v1", "id": {"not_in": ["c1", "c2"]}}
    )
    first = db.captiontrack.upsert.call_args_list[0].kwargs["data"]["create"]
    assert first["id"] == "c1" and first["isCc"] is True and first["name"] is None
    second = db.captiontrack.upsert.call_args_list[1].kwargs["data"]["create"]
    assert second["trackKind"] == "asr" and second["lastUpdated"].year == 2026


@pytest.mark.anyio
async def test_fetch_captions_stores_a_missing_video_first(monkeypatch):
    fake_db(monkeypatch, youtube_caption_service, video_count=0)
    monkeypatch.setattr(youtube_client_service, "fetch_captions", AsyncMock(return_value={"items": []}))
    monkeypatch.setattr(youtube_video_service, "fetch_video", AsyncMock(return_value=(SimpleNamespace(), 2)))

    _, quota = await youtube_caption_service.fetch_video_captions("v1")

    assert quota == 52


def test_captions_route_maps_missing_video_to_404(monkeypatch):
    monkeypatch.setattr(
        youtube_caption_service, "fetch_video_captions", AsyncMock(side_effect=ResourceNotFoundError("gone"))
    )
    assert client.post("/videos/v1/captions/fetch", headers=HEADERS).status_code == 404


def test_list_captions_of_unknown_video_is_404(monkeypatch):
    monkeypatch.setattr(youtube_caption_service, "video_exists", AsyncMock(return_value=False))
    assert client.get("/videos/v1/captions", headers=HEADERS).status_code == 404


@pytest.mark.anyio
async def test_fetch_categories_stores_them_for_the_region(monkeypatch):
    db = fake_db(monkeypatch, youtube_category_service)
    items = [
        {"id": "10", "snippet": {"title": "Music", "assignable": True, "channelId": "UCBR"}},
        {"id": "bad", "snippet": {}},
    ]
    api = AsyncMock(return_value={"items": items})
    monkeypatch.setattr(youtube_client_service, "fetch_video_categories", api)

    _, quota = await youtube_category_service.fetch_video_categories("PK", "ur")

    assert quota == 1
    api.assert_awaited_once_with(region_code="PK", hl="ur")
    assert db.videocategory.upsert.await_count == 1  # the item without a title is skipped
    create = db.videocategory.upsert.call_args.kwargs["data"]["create"]
    assert create == {
        "id": "10",
        "title": "Music",
        "assignable": True,
        "channelId": "UCBR",
        "regionCode": "PK",
        "language": "ur",
        "fetchedAt": create["fetchedAt"],
    }


def test_categories_route_rejects_a_bad_region():
    response = client.post("/video-categories/fetch", json={"region_code": "PAK"}, headers=HEADERS)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_category_name_uses_the_stored_list_before_the_api(monkeypatch):
    youtube_video_service._category_cache.clear()
    monkeypatch.setattr(
        youtube_category_service, "get_stored_category_title", AsyncMock(return_value="Gaming")
    )
    api = AsyncMock()
    monkeypatch.setattr(youtube_client_service, "fetch_video_categories", api)

    assert await youtube_video_service.get_category_name("20") == "Gaming"
    api.assert_not_called()
    youtube_video_service._category_cache.clear()


@pytest.mark.anyio
async def test_category_name_still_works_when_storing_fails(monkeypatch):
    youtube_video_service._category_cache.clear()
    monkeypatch.setattr(
        youtube_category_service, "get_stored_category_title", AsyncMock(side_effect=RuntimeError)
    )
    monkeypatch.setattr(
        youtube_client_service,
        "fetch_video_categories",
        AsyncMock(return_value={"items": [{"id": "27", "snippet": {"title": "Education"}}]}),
    )
    monkeypatch.setattr(youtube_category_service, "store_categories", AsyncMock(side_effect=RuntimeError))

    assert await youtube_video_service.get_category_name("27") == "Education"
    youtube_video_service._category_cache.clear()


@pytest.mark.anyio
async def test_fetch_channel_sections_stores_them_in_order(monkeypatch):
    from services import channel_service, youtube_channel_section_service

    db = MagicMock()
    db.channelsection.delete_many = AsyncMock()
    db.channelsection.upsert = AsyncMock()
    db.channelsection.find_many = AsyncMock(return_value=[])

    class Tx:
        channelsection = db.channelsection

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    db.tx = Tx
    monkeypatch.setattr(youtube_channel_section_service, "database", db)
    monkeypatch.setattr(
        channel_service, "fetch_channel", AsyncMock(return_value=(SimpleNamespace(), 1, False))
    )
    items = [
        {"id": "s1", "snippet": {"type": "popularUploads", "position": 0}},
        {
            "id": "s2",
            "snippet": {"type": "multiplePlaylists", "title": "Series", "position": 1},
            "contentDetails": {"playlists": ["PL1", "PL2"]},
        },
    ]
    monkeypatch.setattr(
        youtube_client_service, "fetch_channel_sections", AsyncMock(return_value={"items": items})
    )

    _, quota = await youtube_channel_section_service.fetch_channel_sections("UC1")

    assert quota == 2  # channel (not stored yet) + sections
    db.channelsection.delete_many.assert_awaited_once_with(
        where={"channelId": "UC1", "id": {"not_in": ["s1", "s2"]}}
    )
    first = db.channelsection.upsert.call_args_list[0].kwargs["data"]["create"]
    assert first["type"] == "popularUploads" and first["title"] is None and first["playlistIds"] == []
    second = db.channelsection.upsert.call_args_list[1].kwargs["data"]["create"]
    assert second["title"] == "Series" and second["playlistIds"] == ["PL1", "PL2"] and second["position"] == 1


def test_list_sections_of_unknown_channel_is_404(monkeypatch):
    from services import youtube_channel_section_service

    monkeypatch.setattr(youtube_channel_section_service, "channel_exists", AsyncMock(return_value=False))
    assert client.get("/channels/UC1/sections", headers=HEADERS).status_code == 404
