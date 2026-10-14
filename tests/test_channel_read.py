from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from application import app
from services import channel_read_service
from validators.channel_read_validator import VideoListQuery

client = TestClient(app)
HEADERS = {"X-API-Key": "test-client-key"}
NOW = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)


def make_channel(**overrides):
    fields = dict(
        id="UC1",
        title="Channel",
        description=None,
        customUrl="@channel",
        country="PK",
        publishedAt=NOW,
        subscriberCount=None,
        subscriberCountHidden=True,
        viewCount=10,
        videoCount=1,
        keywords=[],
        topicCategories=[],
        uploadsPlaylistId="UU1",
        tracked=False,
        fetchedAt=NOW,
        createdAt=NOW,
        updatedAt=NOW,
    )
    return SimpleNamespace(**(fields | overrides))


def make_video(**overrides):
    fields = dict(
        id="v1",
        channelId="UC1",
        title="Video",
        description=None,
        tags=[],
        publishedAt=NOW,
        durationIso="PT30S",
        durationSeconds=30,
        isShort=True,
        uploadGapSeconds=None,
        viewCount=5,
        likeCount=None,
        commentCount=None,
        categoryId=None,
        categoryName=None,
        defaultLanguage=None,
        defaultAudioLanguage=None,
        definition="hd",
        captionsAvailable=False,
        madeForKids=False,
        liveScheduledStartAt=None,
        liveActualStartAt=None,
        liveActualEndAt=None,
        transcriptStatus="pending",
        fetchedAt=NOW,
        createdAt=NOW,
        updatedAt=NOW,
    )
    return SimpleNamespace(**(fields | overrides))


def stub(monkeypatch, name, value):
    async def fake(*_args, **_kwargs):
        return value

    monkeypatch.setattr(channel_read_service, name, fake)


def test_read_endpoints_require_client_key():
    assert client.get("/channels").status_code == 401
    assert client.get("/videos/v1").status_code == 401


def test_list_channels_is_paginated_with_snake_case_fields(monkeypatch):
    stub(monkeypatch, "list_channels", ([make_channel()], 3))

    response = client.get("/channels?page=2&page_size=1", headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert (body["page"], body["page_size"], body["total"]) == (2, 1, 3)
    channel = body["items"][0]
    assert channel["subscriber_count"] is None
    assert channel["subscriber_count_hidden"] is True
    assert channel["published_at"] == "2026-10-02T12:00:00Z"


def test_get_channel_not_found(monkeypatch):
    stub(monkeypatch, "get_channel", None)

    response = client.get("/channels/UCmissing", headers=HEADERS)

    assert response.status_code == 404
    assert response.json() == {"detail": "Channel not found"}


def test_get_video_labels_shorts_flag_as_heuristic(monkeypatch):
    stub(monkeypatch, "get_video", make_video())

    body = client.get("/videos/v1", headers=HEADERS).json()

    assert body["is_short"] is True
    assert body["is_short_label"] == "heuristic"
    assert body["transcript_status"] == "pending"


def test_list_videos_for_unknown_channel(monkeypatch):
    stub(monkeypatch, "channel_exists", False)

    assert client.get("/channels/UCmissing/videos", headers=HEADERS).status_code == 404


def test_list_videos_returns_page(monkeypatch):
    stub(monkeypatch, "channel_exists", True)
    stub(monkeypatch, "list_videos", ([make_video(), make_video(id="v2")], 2))

    body = client.get("/channels/UC1/videos?sort_by=like_count", headers=HEADERS).json()

    assert [video["id"] for video in body["items"]] == ["v1", "v2"]
    assert body["total"] == 2


@pytest.mark.parametrize(
    "query",
    [
        "page=0",
        "page_size=101",
        "sort_by=title",
        "order=up",
        "published_after=2026-05-01T00:00:00Z&published_before=2026-01-01T00:00:00Z",
    ],
)
def test_list_videos_rejects_invalid_query(monkeypatch, query):
    stub(monkeypatch, "channel_exists", True)

    assert client.get(f"/channels/UC1/videos?{query}", headers=HEADERS).status_code == 422


def test_video_filter_combines_shorts_dates_and_live():
    after = datetime(2026, 1, 1, tzinfo=UTC)
    query = VideoListQuery(is_short=False, is_live=True, published_after=after)

    where = channel_read_service.build_video_filter("UC1", query)

    assert where["channelId"] == "UC1"
    assert where["isShort"] is False
    assert where["publishedAt"] == {"gte": after}
    assert where["OR"] == [{"liveScheduledStartAt": {"not": None}}, {"liveActualStartAt": {"not": None}}]


def test_video_filter_excludes_live_streams():
    where = channel_read_service.build_video_filter("UC1", VideoListQuery(is_live=False))

    assert where["liveScheduledStartAt"] is None
    assert where["liveActualStartAt"] is None
    assert "isShort" not in where
