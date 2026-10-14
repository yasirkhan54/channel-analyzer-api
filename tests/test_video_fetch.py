from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from application import app
from services import channel_service, youtube_client_service, youtube_video_service
from services.youtube_client_service import QuotaExhaustedError, ResourceNotFoundError
from tests.test_channel_read import make_video

client = TestClient(app)
HEADERS = {"X-API-Key": "test-client-key"}


def _upload(video_id):
    return {"snippet": {"resourceId": {"videoId": video_id}}}


@pytest.mark.anyio
async def test_fetch_channel_videos_stops_at_max(monkeypatch):
    async def fake_channel(channel_id, force_refresh=False):
        return SimpleNamespace(id=channel_id, uploadsPlaylistId="UU1"), 0, True

    calls = []

    async def fake_items(playlist_id, page_token=None, max_results=50, **kwargs):
        calls.append((playlist_id, max_results))
        start = len(calls) * 100
        return {"items": [_upload(f"v{start + i}") for i in range(max_results)], "nextPageToken": "more"}

    stored = {}

    async def fake_store(video_ids):
        stored["ids"] = video_ids
        return len(video_ids), 0, 2

    async def fake_find(video_ids):
        return [SimpleNamespace(id=v) for v in video_ids]

    monkeypatch.setattr(channel_service, "fetch_channel", fake_channel)
    monkeypatch.setattr(youtube_client_service, "fetch_playlist_items", fake_items)
    monkeypatch.setattr(youtube_video_service, "store_videos_by_id", fake_store)
    monkeypatch.setattr(youtube_video_service, "_find_videos", fake_find)

    videos, quota = await youtube_video_service.fetch_channel_videos("UC1", max_videos=60)

    assert calls == [("UU1", 50), ("UU1", 10)]  # second page asks only for what is left
    assert len(stored["ids"]) == 60
    assert len(videos) == 60
    assert quota == 2 + 2  # two list pages + details


@pytest.mark.anyio
async def test_fetch_video_stores_channel_first(monkeypatch):
    async def fake_videos(id, **kwargs):
        return {"items": [{"id": id[0], "snippet": {"channelId": "UCnew", "title": "T"}}]}

    async def fake_channel(channel_id, force_refresh=False):
        assert channel_id == "UCnew"
        return SimpleNamespace(id=channel_id), 1, False

    upserts = []

    async def fake_upsert(video_id, channel_id, record):
        upserts.append((video_id, channel_id))

    async def noop(*_args, **_kwargs):
        return None

    async def fake_find(video_ids):
        return [SimpleNamespace(id=video_ids[0])]

    monkeypatch.setattr(youtube_client_service, "fetch_videos", fake_videos)
    monkeypatch.setattr(channel_service, "fetch_channel", fake_channel)
    monkeypatch.setattr(youtube_video_service, "_upsert_video", fake_upsert)
    monkeypatch.setattr(youtube_video_service, "update_channel_upload_gaps", noop)
    monkeypatch.setattr(youtube_video_service, "get_category_name", noop)
    monkeypatch.setattr(youtube_video_service, "_find_videos", fake_find)

    video, quota = await youtube_video_service.fetch_video("vid1")

    assert video.id == "vid1"
    assert upserts == [("vid1", "UCnew")]
    assert quota == 2  # video + new channel


@pytest.mark.anyio
async def test_fetch_video_not_found(monkeypatch):
    async def fake_videos(id, **kwargs):
        return {"items": []}

    monkeypatch.setattr(youtube_client_service, "fetch_videos", fake_videos)
    with pytest.raises(ResourceNotFoundError):
        await youtube_video_service.fetch_video("missing")


def test_fetch_endpoints(monkeypatch):
    video = make_video()

    async def fake_channel_videos(channel_id, max_videos):
        assert max_videos == 5
        return [video], 2

    async def fake_video(video_id):
        return video, 1

    monkeypatch.setattr(youtube_video_service, "fetch_channel_videos", fake_channel_videos)
    monkeypatch.setattr(youtube_video_service, "fetch_video", fake_video)

    body = client.post("/channels/UC1/videos/fetch", headers=HEADERS, json={"max_videos": 5}).json()
    assert body["videos_saved"] == 1
    assert body["quota_spent"] == 2

    body = client.post("/videos/v1/fetch", headers=HEADERS).json()
    assert body["quota_spent"] == 1
    assert body["video"]["id"] == video.id

    assert (
        client.post("/channels/UC1/videos/fetch", headers=HEADERS, json={"max_videos": 0}).status_code == 422
    )
    assert client.post("/videos/v1/fetch").status_code == 401


def test_fetch_endpoint_errors(monkeypatch):
    async def not_found(*_args, **_kwargs):
        raise ResourceNotFoundError("not found")

    async def no_quota(*_args, **_kwargs):
        raise QuotaExhaustedError("quota")

    monkeypatch.setattr(youtube_video_service, "fetch_video", not_found)
    assert client.post("/videos/x/fetch", headers=HEADERS).status_code == 404
    monkeypatch.setattr(youtube_video_service, "fetch_channel_videos", no_quota)
    assert client.post("/channels/UC1/videos/fetch", headers=HEADERS, json={}).status_code == 429


def _thread(comment_id, replies=0):
    return {
        "snippet": {
            "totalReplyCount": replies,
            "topLevelComment": {"id": comment_id, "snippet": {"textDisplay": comment_id, "likeCount": 1}},
        },
        "replies": {"comments": [{"id": f"{comment_id}.r{i}", "snippet": {}} for i in range(replies)]},
    }


@pytest.mark.anyio
async def test_fetch_video_comments_limit_and_replies(monkeypatch):
    from services import youtube_comment_service

    calls = []

    async def fake_threads(video_id, order="relevance", max_results=100, page_token=None, **kwargs):
        calls.append((order, max_results))
        return {
            "items": [_thread(f"c{len(calls)}-{i}", replies=1) for i in range(max_results)],
            "nextPageToken": "n",
        }

    saved = []

    async def fake_upsert(comment_id, record):
        saved.append((comment_id, record["parentId"]))

    monkeypatch.setattr(youtube_client_service, "fetch_comment_threads", fake_threads)
    monkeypatch.setattr(youtube_comment_service, "_upsert_comment", fake_upsert)

    top, replies, quota, disabled = await youtube_comment_service.fetch_video_comments(
        "v1", 150, order="time"
    )

    assert calls == [("time", 100), ("time", 50)]
    assert (top, replies, quota, disabled) == (150, 150, 2, False)

    saved.clear()
    top, replies, _, _ = await youtube_comment_service.fetch_video_comments("v1", 3, include_replies=False)
    assert (top, replies) == (3, 0)
    assert all(parent is None for _, parent in saved)


@pytest.mark.anyio
async def test_fetch_video_comments_disabled(monkeypatch):
    from services import youtube_comment_service

    async def disabled(*_args, **_kwargs):
        raise youtube_client_service.YouTubeAPIError("commentsDisabled")

    monkeypatch.setattr(youtube_client_service, "fetch_comment_threads", disabled)

    assert await youtube_comment_service.fetch_video_comments("v1", 10) == (0, 0, 0, True)


@pytest.mark.anyio
async def test_fetch_comments_for_unstored_video_stores_it_first(monkeypatch):
    from services import youtube_comment_service

    async def not_stored(video_id):
        return False

    async def fake_fetch_video(video_id):
        return SimpleNamespace(id=video_id), 2

    async def fake_comments(video_id, max_comments, include_replies, order):
        return 5, 1, 1, False

    monkeypatch.setattr(youtube_comment_service, "_video_is_stored", not_stored)
    monkeypatch.setattr(youtube_video_service, "fetch_video", fake_fetch_video)
    monkeypatch.setattr(youtube_comment_service, "fetch_video_comments", fake_comments)

    assert await youtube_comment_service.fetch_comments_for_video("v1", 5) == (5, 1, 3, False)


def test_comment_fetch_endpoint_and_videos_with_comments(monkeypatch):
    from services import youtube_comment_service

    async def fake_for_video(video_id, max_comments, include_replies, order):
        assert (max_comments, include_replies, order) == (20, False, "time")
        return 20, 0, 1, False

    monkeypatch.setattr(youtube_comment_service, "fetch_comments_for_video", fake_for_video)
    body = client.post(
        "/videos/v1/comments/fetch",
        headers=HEADERS,
        json={"max_comments": 20, "include_replies": False, "order": "time"},
    ).json()
    assert body == {
        "video_id": "v1",
        "comments_saved": 20,
        "replies_saved": 0,
        "comments_disabled": False,
        "quota_spent": 1,
    }
    assert client.post("/videos/v1/comments/fetch", headers=HEADERS, json={"order": "top"}).status_code == 422

    async def fake_channel_videos(channel_id, max_videos):
        return [make_video(id="a"), make_video(id="b")], 2

    async def fake_comments(video_id, max_comments):
        return max_comments, 1, 1, False

    monkeypatch.setattr(youtube_video_service, "fetch_channel_videos", fake_channel_videos)
    monkeypatch.setattr(youtube_comment_service, "fetch_video_comments", fake_comments)
    body = client.post(
        "/channels/UC1/videos/fetch", headers=HEADERS, json={"max_videos": 2, "comments_per_video": 10}
    ).json()
    assert body["comments_saved"] == 22
    assert body["quota_spent"] == 4
