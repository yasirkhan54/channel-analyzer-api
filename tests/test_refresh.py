import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from prisma.enums import CommentMode, FetchJobStatus, FetchJobType, TranscriptStepStatus

from application import app
from services import channel_service, fetch_job_service, refresh_service, youtube_client_service
from tests.test_channel_read import make_channel

client = TestClient(app)
HEADERS = {"X-API-Key": "test-client-key"}


def make_job(**overrides):
    fields = dict(
        id=12,
        channel_input="UC1",
        channel_id=None,
        type=FetchJobType.full_refresh,
        comment_mode=CommentMode.top_100,
        status=FetchJobStatus.queued,
        stage=None,
        transcripts_requested=False,
        transcript_step_status=TranscriptStepStatus.not_requested,
        videos_found=0,
        videos_done=0,
        comments_fetched=0,
        playlists_done=0,
        transcripts_done=0,
        transcripts_missing=0,
        transcripts_blocked=0,
        resume_cursor=None,
        quota_spent=0,
        error_detail=None,
        started_at=None,
        finished_at=None,
        created_at=make_channel().createdAt,
        updated_at=make_channel().updatedAt,
    )
    return fields | overrides


def stub(monkeypatch, module, name, value):
    async def fake(*_args, **_kwargs):
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(module, name, fake)


def test_stats_refresh_endpoint(monkeypatch):
    stub(monkeypatch, refresh_service, "refresh_channel_stats", (make_channel(), 3, 2))

    response = client.post("/channels/UC1/refresh/stats", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["videos_refreshed"] == 3
    assert response.json()["quota_spent"] == 2


def test_stats_refresh_channel_not_found(monkeypatch):
    stub(monkeypatch, refresh_service, "refresh_channel_stats", refresh_service.StoredChannelNotFoundError())

    assert client.post("/channels/unknown/refresh/stats", headers=HEADERS).status_code == 404


def test_full_refresh_queues_job(monkeypatch):
    stub(monkeypatch, refresh_service, "queue_full_refresh", make_job())

    response = client.post(
        "/channels/UC1/refresh/full",
        headers=HEADERS,
        json={"comment_mode": "all", "transcripts_requested": False},
    )

    assert response.status_code == 201
    assert response.json()["job"]["type"] == "full_refresh"


def test_full_refresh_unknown_channel(monkeypatch):
    stub(monkeypatch, refresh_service, "queue_full_refresh", refresh_service.StoredChannelNotFoundError())

    assert client.post("/channels/unknown/refresh/full", headers=HEADERS).status_code == 404


def test_stats_refresh_updates_stored_video_counts_in_batches(monkeypatch):
    channel = make_channel()
    db = SimpleNamespace(
        video=SimpleNamespace(
            find_many=AsyncMock(return_value=[SimpleNamespace(id="v1"), SimpleNamespace(id="v2")]),
            update=AsyncMock(),
        )
    )
    monkeypatch.setattr(refresh_service, "database", db)
    stub(monkeypatch, refresh_service, "_get_stored_channel", channel)
    stub(monkeypatch, channel_service, "fetch_channel", (channel, 1, False))
    fetch_videos = AsyncMock(
        return_value={"items": [{"id": "v1", "statistics": {"viewCount": "10", "likeCount": "2"}}]}
    )
    monkeypatch.setattr(youtube_client_service, "fetch_videos", fetch_videos)

    refreshed_channel, videos_refreshed, quota_spent = asyncio.run(
        refresh_service.refresh_channel_stats("UC1")
    )

    assert refreshed_channel is channel
    assert (videos_refreshed, quota_spent) == (1, 2)
    assert fetch_videos.await_args.kwargs == {"id": ["v1", "v2"], "part": "statistics"}
    update = db.video.update.await_args.kwargs
    assert update["where"] == {"id": "v1"}
    assert update["data"]["viewCount"] == 10
    assert update["data"]["likeCount"] == 2
    assert update["data"]["commentCount"] is None


def test_queue_full_refresh_uses_fetch_job_service(monkeypatch):
    channel = make_channel()
    job = make_job()
    stub(monkeypatch, refresh_service, "_get_stored_channel", channel)
    create = AsyncMock(return_value=job)
    monkeypatch.setattr(fetch_job_service, "create_fetch_job", create)

    result = asyncio.run(refresh_service.queue_full_refresh("UC1", CommentMode.skip, False))

    assert result == job
    assert create.await_args.kwargs == {
        "channel_input": "UC1",
        "comment_mode": CommentMode.skip,
        "job_type": FetchJobType.full_refresh,
        "transcripts_requested": False,
    }
