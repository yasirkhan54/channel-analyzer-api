import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from prisma.enums import CommentMode, FetchJobStatus, FetchJobType, TranscriptStepStatus

from application import app
from services import fetch_job_service, search_service, youtube_client_service
from services.youtube_client_service import QuotaExhaustedError, YouTubeRequestError
from validators.search_validator import SearchRequest

client = TestClient(app)
HEADERS = {"X-API-Key": "test-client-key"}
NOW = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)


def make_job(**overrides):
    fields = dict(
        id=11,
        channel_input="UC1",
        channel_id=None,
        type=FetchJobType.full_fetch,
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
        created_at=NOW,
        updated_at=NOW,
    )
    return fields | overrides


def stub(monkeypatch, module, name, value):
    async def fake(*_args, **_kwargs):
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(module, name, fake)


def test_estimate_reports_cost_and_availability(monkeypatch):
    stub(monkeypatch, search_service, "get_units_available", 250)

    response = client.post("/search/estimate", json={"keyword": "cooking", "pages": 3}, headers=HEADERS)

    assert response.json() == {"quota_cost": 300, "units_available": 250, "allowed": False}


def test_search_refused_when_quota_too_low(monkeypatch):
    stub(monkeypatch, search_service, "get_units_available", 99)

    async def must_not_call(*_args, **_kwargs):
        raise AssertionError("search.list must not be called")

    monkeypatch.setattr(youtube_client_service, "fetch_search", must_not_call)

    response = client.post("/search", json={"keyword": "cooking"}, headers=HEADERS)

    assert response.status_code == 429
    assert "needs 100 quota units but only 99" in response.json()["detail"]


def test_search_refused_when_youtube_reports_quota_exceeded(monkeypatch):
    stub(monkeypatch, search_service, "run_search", QuotaExhaustedError("quotaExceeded"))

    assert client.post("/search", json={"keyword": "cooking"}, headers=HEADERS).status_code == 429


def test_search_hides_youtube_error_text(monkeypatch):
    stub(monkeypatch, search_service, "run_search", YouTubeRequestError("400 ... key=secret"))

    response = client.post("/search", json={"keyword": "cooking"}, headers=HEADERS)

    assert response.status_code == 502
    assert "secret" not in response.text


def test_search_returns_stored_query_with_results(monkeypatch):
    stored = SimpleNamespace(
        id=7,
        keyword="cooking",
        type="channel",
        filters={"order": "relevance", "pages": 1, "results_per_page": 50},
        quotaSpent=100,
        fetchedAt=NOW,
        createdAt=NOW,
        results=[
            SimpleNamespace(rank=1, resultType="channel", videoId=None, channelId="UC1", title="Chef"),
        ],
    )
    stub(monkeypatch, search_service, "run_search", stored)

    response = client.post("/search", json={"keyword": "cooking", "type": "channel"}, headers=HEADERS)

    assert response.status_code == 201
    body = response.json()
    assert body["quota_spent"] == 100
    assert body["results"][0] == {
        "rank": 1,
        "result_type": "channel",
        "video_id": None,
        "channel_id": "UC1",
        "title": "Chef",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"keyword": ""},
        {"keyword": "x", "pages": 6},
        {"keyword": "x", "results_per_page": 51},
        {"keyword": "x", "type": "playlist"},
        {"keyword": "x", "region_code": "PAK"},
        {"keyword": "x", "published_after": "2026-05-01T00:00Z", "published_before": "2026-01-01T00:00Z"},
    ],
)
def test_search_rejects_invalid_request(payload):
    assert client.post("/search", json=payload, headers=HEADERS).status_code == 422


def test_search_not_found(monkeypatch):
    stub(monkeypatch, search_service, "get_search", None)

    assert client.get("/searches/5", headers=HEADERS).status_code == 404


def test_queue_search_result_for_full_fetch(monkeypatch):
    stub(monkeypatch, search_service, "queue_search_result_for_full_fetch", make_job())

    response = client.post(
        "/searches/7/results/2/queue",
        headers=HEADERS,
        json={"comment_mode": "skip", "transcripts_requested": False},
    )

    assert response.status_code == 201
    assert response.json()["job"]["type"] == "full_fetch"
    assert response.json()["job"]["channel_input"] == "UC1"


def test_queue_search_result_handles_missing_and_unqueueable_results(monkeypatch):
    stub(
        monkeypatch,
        search_service,
        "queue_search_result_for_full_fetch",
        search_service.SearchResultNotFoundError(),
    )
    assert client.post("/searches/7/results/2/queue", headers=HEADERS).status_code == 404

    stub(
        monkeypatch,
        search_service,
        "queue_search_result_for_full_fetch",
        search_service.SearchResultWithoutChannelError(),
    )
    assert client.post("/searches/7/results/2/queue", headers=HEADERS).status_code == 422


def test_queue_search_result_uses_result_channel_and_fetch_job_service(monkeypatch):
    db = SimpleNamespace(
        searchresult=SimpleNamespace(
            find_unique=AsyncMock(return_value=SimpleNamespace(channelId="UCresult"))
        )
    )
    create = AsyncMock(return_value=make_job())
    monkeypatch.setattr(search_service, "database", db)
    monkeypatch.setattr(fetch_job_service, "create_fetch_job", create)

    job = asyncio.run(
        search_service.queue_search_result_for_full_fetch(4, 2, CommentMode.skip, transcripts_requested=False)
    )

    assert job["channel_input"] == "UC1"
    assert db.searchresult.find_unique.await_args.kwargs == {
        "where": {"searchQueryId_rank": {"searchQueryId": 4, "rank": 2}}
    }
    assert create.await_args.kwargs == {
        "channel_input": "UCresult",
        "comment_mode": CommentMode.skip,
        "job_type": FetchJobType.full_fetch,
        "transcripts_requested": False,
    }


def test_parse_search_items_ranks_videos_and_channels():
    video = {"kind": "youtube#video", "videoId": "v1"}
    channel = {"kind": "youtube#channel", "channelId": "UC2"}
    items = [
        {"id": video, "snippet": {"channelId": "UC1", "title": "Tom &amp; Jerry"}},
        {"id": {"kind": "youtube#playlist", "playlistId": "PL1"}, "snippet": {"title": "skipped"}},
        {"id": channel, "snippet": {"channelId": "UC2", "title": "Chef"}},
    ]

    results = search_service.parse_search_items(items, first_rank=51)

    assert results == [
        {"resultType": "video", "videoId": "v1", "channelId": "UC1", "rank": 51, "title": "Tom & Jerry"},
        {"resultType": "channel", "videoId": None, "channelId": "UC2", "rank": 52, "title": "Chef"},
    ]


def test_build_search_params_formats_filters():
    request = SearchRequest(
        keyword="x",
        region_code="pk",
        relevance_language="ur",
        published_after=datetime(2026, 1, 1, 5, 0, tzinfo=UTC),
        order="date",
    )

    assert search_service.build_search_params(request) == {
        "order": "date",
        "regionCode": "PK",
        "relevanceLanguage": "ur",
        "publishedAfter": "2026-01-01T05:00:00Z",
    }


def test_run_search_raises_before_calling_youtube_when_quota_low(monkeypatch):
    stub(monkeypatch, search_service, "get_units_available", 150)

    with pytest.raises(search_service.InsufficientQuotaError):
        asyncio.run(search_service.run_search(SearchRequest(keyword="x", pages=2)))
