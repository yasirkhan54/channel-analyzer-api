from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from application import app
from services import (
    channel_read_service,
    comment_read_service,
    playlist_read_service,
    youtube_playlist_service,
)
from services.youtube_client_service import QuotaExhaustedError, ResourceNotFoundError
from tests.test_channel_read import make_video

client = TestClient(app)
HEADERS = {"X-API-Key": "test-client-key"}
NOW = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)


def make_comment(**overrides):
    fields = dict(
        id="c1",
        videoId="v1",
        parentId=None,
        text="Nice",
        authorDisplayName="Ali",
        authorChannelId="UCa",
        likeCount=3,
        totalReplyCount=1,
        publishedAt=NOW,
        editedAt=None,
        fetchedAt=NOW,
        replies=[],
    )
    return SimpleNamespace(**(fields | overrides))


def stub(monkeypatch, module, name, value):
    async def fake(*_args, **_kwargs):
        return value

    monkeypatch.setattr(module, name, fake)


def test_comment_threads_include_replies(monkeypatch):
    reply = make_comment(id="c1r1", parentId="c1", totalReplyCount=None, replies=None)
    stub(monkeypatch, comment_read_service, "video_exists", True)
    stub(monkeypatch, comment_read_service, "list_comment_threads", ([make_comment(replies=[reply])], 1))

    response = client.get("/videos/v1/comments?sort_by=published_at&order=asc", headers=HEADERS)

    assert response.status_code == 200
    thread = response.json()["items"][0]
    assert thread["id"] == "c1"
    assert [r["parent_id"] for r in thread["replies"]] == ["c1"]


def test_comments_for_unknown_video(monkeypatch):
    stub(monkeypatch, comment_read_service, "video_exists", False)

    assert client.get("/videos/missing/comments", headers=HEADERS).status_code == 404


def test_comments_reject_unknown_sort(monkeypatch):
    stub(monkeypatch, comment_read_service, "video_exists", True)

    assert client.get("/videos/v1/comments?sort_by=text", headers=HEADERS).status_code == 422


def test_channel_playlists(monkeypatch):
    playlist = SimpleNamespace(
        id="PL1",
        channelId="UC1",
        title="Best of",
        description=None,
        publishedAt=None,
        itemCount=2,
        fetchedAt=NOW,
        createdAt=NOW,
        updatedAt=NOW,
    )
    stub(monkeypatch, channel_read_service, "channel_exists", True)
    stub(monkeypatch, playlist_read_service, "list_playlists", ([playlist], 1))

    body = client.get("/channels/UC1/playlists", headers=HEADERS).json()

    assert body["items"][0]["item_count"] == 2
    assert body["total"] == 1


def test_playlist_videos_embed_stored_video(monkeypatch):
    def item(item_id, video_id, available):
        return SimpleNamespace(
            id=item_id,
            playlistId="PL1",
            videoId=video_id,
            position=0,
            videoAvailable=available,
            fetchedAt=NOW,
        )

    pairs = [(item("i1", "v1", True), make_video()), (item("i2", "gone", False), None)]
    stub(monkeypatch, playlist_read_service, "playlist_exists", True)
    stub(monkeypatch, playlist_read_service, "list_playlist_items", (pairs, 2))

    items = client.get("/playlists/PL1/videos", headers=HEADERS).json()["items"]

    assert items[0]["video"]["is_short_label"] == "heuristic"
    assert items[1]["video"] is None
    assert items[1]["video_available"] is False


def test_playlist_not_found(monkeypatch):
    stub(monkeypatch, playlist_read_service, "playlist_exists", False)

    assert client.get("/playlists/missing/videos", headers=HEADERS).status_code == 404


def test_fetch_channel_playlists_endpoint(monkeypatch):
    playlist = SimpleNamespace(
        id="PL1",
        channelId="UC1",
        title="Best of",
        description=None,
        publishedAt=None,
        itemCount=2,
        fetchedAt=NOW,
        createdAt=NOW,
        updatedAt=NOW,
    )
    seen = {}

    async def fake(channel_id, max_playlists, include_videos):
        seen.update(channel_id=channel_id, max_playlists=max_playlists, include_videos=include_videos)
        return youtube_playlist_service.PlaylistFetchResult(playlists=[playlist], quota_spent=1)

    monkeypatch.setattr(youtube_playlist_service, "fetch_channel_playlists", fake)

    response = client.post("/channels/UC1/playlists/fetch", headers=HEADERS, json={"max_playlists": 10})

    assert response.status_code == 200
    body = response.json()
    assert seen == {"channel_id": "UC1", "max_playlists": 10, "include_videos": False}
    assert body["playlists_saved"] == 1
    assert body["quota_spent"] == 1
    assert body["playlists"][0]["id"] == "PL1"


def test_fetch_channel_playlists_defaults_and_limits(monkeypatch):
    stub(
        monkeypatch,
        youtube_playlist_service,
        "fetch_channel_playlists",
        youtube_playlist_service.PlaylistFetchResult(quota_spent=1),
    )

    assert client.post("/channels/UC1/playlists/fetch", headers=HEADERS).status_code == 422  # body required
    assert (
        client.post("/channels/UC1/playlists/fetch", headers=HEADERS, json={}).json()["playlists_saved"] == 0
    )
    bad = client.post("/channels/UC1/playlists/fetch", headers=HEADERS, json={"max_playlists": 0})
    assert bad.status_code == 422
    assert client.post("/channels/UC1/playlists/fetch", json={}).status_code == 401


def test_fetch_channel_playlists_errors(monkeypatch):
    async def not_found(*_args, **_kwargs):
        raise ResourceNotFoundError("YouTube channel UCx not found")

    monkeypatch.setattr(youtube_playlist_service, "fetch_channel_playlists", not_found)
    assert client.post("/channels/UCx/playlists/fetch", headers=HEADERS, json={}).status_code == 404

    async def no_quota(*_args, **_kwargs):
        raise QuotaExhaustedError("Daily quota exhausted")

    monkeypatch.setattr(youtube_playlist_service, "fetch_channel_playlists", no_quota)
    assert client.post("/channels/UC1/playlists/fetch", headers=HEADERS, json={}).status_code == 429
