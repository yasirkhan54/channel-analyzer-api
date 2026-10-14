from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from prisma.enums import (
    CommentMode,
    FetchJobStage,
    FetchJobStatus,
    FetchJobType,
    TranscriptStepStatus,
)

from application import app
from services import fetch_adapters, fetch_job_runner, fetch_job_service
from services.fetch_adapters import calculate_job_estimate
from services.youtube_client_service import QuotaExhaustedError

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-client-key"}


def test_calculate_job_estimate():
    # Channels under 200 videos: transcripts on by default (R-24)
    est_small = calculate_job_estimate(
        video_count=50,
        comment_mode="top_100",
        transcripts_requested=True,
    )
    assert est_small["video_count"] == 50
    assert est_small["transcripts_requested"] is True
    # 50 videos * 2s = 100s
    assert est_small["estimated_transcript_time_seconds"] == 100
    assert est_small["estimated_transcript_time_formatted"] == "1m 40s"
    assert est_small["estimated_quota_units_min"] > 0
    assert est_small["estimated_quota_units_max"] >= est_small["estimated_quota_units_min"]

    # Channels with skip comments: 0 comment cost
    est_skip = calculate_job_estimate(
        video_count=100,
        comment_mode="skip",
        transcripts_requested=False,
    )
    assert est_skip["estimated_transcript_time_seconds"] == 0
    # Channel (1) + Videos (4) + Playlists (1) = 6 units
    assert est_skip["estimated_quota_units_min"] == 6


def test_create_fetch_job_requires_auth():
    resp = client.post("/fetch-jobs", json={"channel_input": "https://youtube.com/@veritasium"})
    assert resp.status_code == 401


def test_create_fetch_job_success(monkeypatch):
    dummy_job = {
        "id": 42,
        "channel_input": "@veritasium",
        "channel_id": None,
        "type": FetchJobType.full_fetch,
        "comment_mode": CommentMode.top_100,
        "status": FetchJobStatus.queued,
        "stage": None,
        "transcripts_requested": False,
        "transcript_step_status": TranscriptStepStatus.not_requested,
        "videos_found": 0,
        "videos_done": 0,
        "comments_fetched": 0,
        "playlists_done": 0,
        "transcripts_done": 0,
        "transcripts_missing": 0,
        "transcripts_blocked": 0,
        "resume_cursor": None,
        "quota_spent": 0,
        "error_detail": None,
        "started_at": None,
        "finished_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    async def mock_create(**kwargs):
        return dummy_job

    monkeypatch.setattr(fetch_job_service, "create_fetch_job", mock_create)
    resp = client.post(
        "/fetch-jobs",
        headers=AUTH_HEADERS,
        json={"channel_input": "@veritasium"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 42
    assert body["channel_input"] == "@veritasium"
    assert body["status"] == "queued"


def test_get_fetch_job(monkeypatch):
    dummy_job = {
        "id": 1,
        "channel_input": "UC123",
        "channel_id": "UC123",
        "type": FetchJobType.full_fetch,
        "comment_mode": CommentMode.top_100,
        "status": FetchJobStatus.running,
        "stage": FetchJobStage.videos,
        "transcripts_requested": True,
        "transcript_step_status": TranscriptStepStatus.pending,
        "videos_found": 150,
        "videos_done": 50,
        "comments_fetched": 0,
        "playlists_done": 0,
        "transcripts_done": 0,
        "transcripts_missing": 0,
        "transcripts_blocked": 0,
        "resume_cursor": {"stage": "videos"},
        "quota_spent": 3,
        "error_detail": None,
        "started_at": datetime.now(UTC),
        "finished_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    async def mock_get(job_id):
        if job_id == 1:
            return dummy_job
        raise fetch_job_service.JobNotFoundError(job_id)

    monkeypatch.setattr(fetch_job_service, "get_fetch_job", mock_get)

    resp = client.get("/fetch-jobs/1", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["id"] == 1
    assert resp.json()["videos_done"] == 50

    resp_404 = client.get("/fetch-jobs/999", headers=AUTH_HEADERS)
    assert resp_404.status_code == 404


def test_cancel_fetch_job(monkeypatch):
    cancelled_job = {
        "id": 2,
        "channel_input": "UC456",
        "channel_id": "UC456",
        "type": FetchJobType.full_fetch,
        "comment_mode": CommentMode.top_100,
        "status": FetchJobStatus.cancelled,
        "stage": FetchJobStage.videos,
        "transcripts_requested": False,
        "transcript_step_status": TranscriptStepStatus.not_requested,
        "videos_found": 100,
        "videos_done": 20,
        "comments_fetched": 0,
        "playlists_done": 0,
        "transcripts_done": 0,
        "transcripts_missing": 0,
        "transcripts_blocked": 0,
        "resume_cursor": None,
        "quota_spent": 2,
        "error_detail": None,
        "started_at": datetime.now(UTC),
        "finished_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    async def mock_cancel(job_id):
        if job_id == 2:
            return cancelled_job
        if job_id == 3:
            raise fetch_job_service.JobAlreadyTerminalError(job_id, "completed")
        raise fetch_job_service.JobNotFoundError(job_id)

    monkeypatch.setattr(fetch_job_service, "cancel_fetch_job", mock_cancel)

    resp = client.post("/fetch-jobs/2/cancel", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    resp_terminal = client.post("/fetch-jobs/3/cancel", headers=AUTH_HEADERS)
    assert resp_terminal.status_code == 400


def test_estimate_fetch_job(monkeypatch):
    dummy_estimate = {
        "channel_id": "UC123",
        "channel_title": "Veritasium",
        "video_count": 120,
        "comment_mode": CommentMode.top_100,
        "estimated_quota_units_min": 130,
        "estimated_quota_units_max": 190,
        "transcripts_requested": True,
        "estimated_transcript_time_seconds": 240,
        "estimated_transcript_time_formatted": "4m 0s",
        "quota_available": True,
        "current_quota_remaining": 9500,
        "warning": None,
    }

    async def mock_est(**kwargs):
        return dummy_estimate

    monkeypatch.setattr(fetch_job_service, "estimate_fetch_job", mock_est)

    resp = client.post(
        "/fetch-jobs/estimate",
        headers=AUTH_HEADERS,
        json={"channel_input": "UC123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["channel_title"] == "Veritasium"
    assert data["estimated_quota_units_min"] == 130
    assert data["quota_available"] is True


@pytest.mark.anyio
async def test_runner_quota_exhaustion_pauses_job(monkeypatch):
    from unittest.mock import MagicMock

    mock_db = MagicMock()
    dummy_job = MagicMock()
    dummy_job.id = 10
    dummy_job.status = FetchJobStatus.running
    dummy_job.startedAt = None
    dummy_job.channelId = "UC10"
    dummy_job.resumeCursor = {"stage": "videos", "uploads_playlist_id": "UU10"}
    dummy_job.transcriptsRequested = False
    dummy_job.transcriptStepStatus = TranscriptStepStatus.not_requested
    dummy_job.commentMode = CommentMode.skip

    mock_db.fetchjob.find_unique = AsyncMock(return_value=dummy_job)
    mock_db.fetchjob.update = AsyncMock()

    monkeypatch.setattr("configurations.database_configuration.database", mock_db)
    monkeypatch.setattr(fetch_job_runner.quota_service, "check_quota_available", AsyncMock(return_value=True))

    async def mock_fetch_videos(*args, **kwargs):
        raise QuotaExhaustedError("Daily quota limit reached")

    monkeypatch.setattr(fetch_adapters, "fetch_videos_page", mock_fetch_videos)

    await fetch_job_runner.execute_job(10)

    # Verify job was paused
    calls = mock_db.fetchjob.update.call_args_list
    paused_calls = [
        c for c in calls if c.kwargs.get("data", {}).get("status") == FetchJobStatus.paused_for_quota
    ]
    assert len(paused_calls) > 0


@pytest.mark.anyio
async def test_runner_stores_channel_id_with_json_cursor(monkeypatch):
    """Prisma rejects a plain dict for the Json resume_cursor, which also dropped the channel ID write."""
    from unittest.mock import MagicMock

    from prisma import Json

    mock_db = MagicMock()
    dummy_job = MagicMock()
    dummy_job.id = 11
    dummy_job.status = FetchJobStatus.queued
    dummy_job.startedAt = None
    dummy_job.channelId = None
    dummy_job.channelInput = "@veritasium"
    dummy_job.type = "full_fetch"
    dummy_job.resumeCursor = None
    dummy_job.transcriptsRequested = False
    dummy_job.transcriptStepStatus = TranscriptStepStatus.not_requested
    dummy_job.commentMode = CommentMode.skip

    mock_db.fetchjob.find_unique = AsyncMock(return_value=dummy_job)
    mock_db.fetchjob.update = AsyncMock()
    monkeypatch.setattr("configurations.database_configuration.database", mock_db)
    monkeypatch.setattr(fetch_job_runner.quota_service, "check_quota_available", AsyncMock(return_value=True))
    monkeypatch.setattr(
        fetch_adapters,
        "resolve_and_fetch_channel",
        AsyncMock(return_value={"id": "UC11", "uploads_playlist_id": "UU11", "video_count": 500}),
    )
    monkeypatch.setattr(
        fetch_adapters, "fetch_videos_page", AsyncMock(side_effect=QuotaExhaustedError("quota"))
    )

    await fetch_job_runner.execute_job(11)

    data = [c.kwargs["data"] for c in mock_db.fetchjob.update.call_args_list]
    channel_update = next(d for d in data if "channelId" in d)
    assert channel_update["channelId"] == "UC11"
    assert all(isinstance(d["resumeCursor"], Json) for d in data if "resumeCursor" in d)
    assert data[-1]["status"] == FetchJobStatus.paused_for_quota


def make_runner_db(monkeypatch, comment_mode, transcripts_requested, videos):
    """A fake database for execute_job that starts after the videos stage."""
    from unittest.mock import MagicMock

    mock_db = MagicMock()
    job = MagicMock()
    job.id = 12
    job.status = FetchJobStatus.queued
    job.startedAt = None
    job.channelId = "UC12"
    job.channelInput = "UC12"
    job.type = "full_fetch"
    job.resumeCursor = {"stage": "videos_done", "uploads_playlist_id": "UU12"}
    job.transcriptsRequested = transcripts_requested
    job.transcriptStepStatus = TranscriptStepStatus.not_requested
    job.commentMode = comment_mode

    mock_db.fetchjob.find_unique = AsyncMock(return_value=job)
    mock_db.fetchjob.update = AsyncMock()
    mock_db.video.find_many = AsyncMock(return_value=videos)
    monkeypatch.setattr("configurations.database_configuration.database", mock_db)
    monkeypatch.setattr(fetch_job_runner.quota_service, "check_quota_available", AsyncMock(return_value=True))
    return mock_db


def video(video_id, comment_count):
    from unittest.mock import MagicMock

    return MagicMock(id=video_id, commentCount=comment_count)


@pytest.mark.anyio
async def test_runner_fetches_comments_playlists_and_skips_unrequested_transcripts(monkeypatch):
    mock_db = make_runner_db(monkeypatch, CommentMode.all, False, [video("v1", 5), video("v2", 0)])
    # v1 has two comment pages; v2 has no comments and is skipped without a call.
    comments = AsyncMock(side_effect=[("page2", 100, 1), (None, 40, 1)])
    playlists = AsyncMock(side_effect=[("next", 50, 3), (None, 7, 2)])
    transcripts = AsyncMock()
    monkeypatch.setattr(fetch_adapters, "fetch_comments_page", comments)
    monkeypatch.setattr(fetch_adapters, "fetch_playlists_page", playlists)
    monkeypatch.setattr(fetch_job_runner.transcript_service, "fetch_and_store_video_transcript", transcripts)

    await fetch_job_runner.execute_job(12)

    assert [c.args for c in comments.call_args_list] == [
        ("v1", CommentMode.all, None),
        ("v1", CommentMode.all, "page2"),
    ]
    assert [c.args for c in playlists.call_args_list] == [("UC12", None), ("UC12", "next")]
    transcripts.assert_not_called()
    data = [c.kwargs["data"] for c in mock_db.fetchjob.update.call_args_list]
    assert sum(d.get("commentsFetched", {}).get("increment", 0) for d in data) == 140
    assert sum(d.get("playlistsDone", {}).get("increment", 0) for d in data) == 57
    assert data[-1]["status"] == FetchJobStatus.completed


@pytest.mark.anyio
async def test_runner_skip_comments_completes_and_runs_requested_transcripts(monkeypatch):
    from unittest.mock import MagicMock

    from prisma.enums import TranscriptStatus

    mock_db = make_runner_db(monkeypatch, CommentMode.skip, True, [video("v1", 5)])
    comments = AsyncMock()
    monkeypatch.setattr(fetch_adapters, "fetch_comments_page", comments)
    monkeypatch.setattr(fetch_adapters, "fetch_playlists_page", AsyncMock(return_value=(None, 0, 1)))
    transcripts = AsyncMock(return_value=MagicMock(status=TranscriptStatus.available))
    monkeypatch.setattr(fetch_job_runner.transcript_service, "fetch_and_store_video_transcript", transcripts)
    monkeypatch.setattr(fetch_job_runner.asyncio, "sleep", AsyncMock())

    await fetch_job_runner.execute_job(12)

    comments.assert_not_called()
    transcripts.assert_awaited_once_with("v1")
    data = [c.kwargs["data"] for c in mock_db.fetchjob.update.call_args_list]
    assert data[-1]["status"] == FetchJobStatus.completed


@pytest.mark.anyio
async def test_runner_skips_comments_of_an_unavailable_video(monkeypatch):
    from services.youtube_client_service import ResourceNotFoundError

    mock_db = make_runner_db(monkeypatch, CommentMode.top_100, False, [video("gone", 3), video("v2", 3)])
    comments = AsyncMock(side_effect=[ResourceNotFoundError("gone"), (None, 20, 1)])
    monkeypatch.setattr(fetch_adapters, "fetch_comments_page", comments)
    monkeypatch.setattr(fetch_adapters, "fetch_playlists_page", AsyncMock(return_value=(None, 0, 1)))

    await fetch_job_runner.execute_job(12)

    assert [c.args[0] for c in comments.call_args_list] == ["gone", "v2"]
    data = [c.kwargs["data"] for c in mock_db.fetchjob.update.call_args_list]
    assert data[-1]["status"] == FetchJobStatus.completed
