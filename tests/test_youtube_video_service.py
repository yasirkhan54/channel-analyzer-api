from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from services import youtube_client_service, youtube_video_service


def test_parse_iso8601_duration():
    assert youtube_video_service.parse_iso8601_duration("PT1H2M30S") == 3750
    assert youtube_video_service.parse_iso8601_duration("PT45S") == 45
    assert youtube_video_service.parse_iso8601_duration("PT1M") == 60
    assert youtube_video_service.parse_iso8601_duration("PT180S") == 180
    assert youtube_video_service.parse_iso8601_duration("P1DT2H") == 93600
    assert youtube_video_service.parse_iso8601_duration("") == 0
    assert youtube_video_service.parse_iso8601_duration(None) == 0


@pytest.mark.anyio
async def test_update_channel_upload_gaps(monkeypatch):
    t0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(days=2, hours=3)
    t2 = t1 + timedelta(hours=5)

    from unittest.mock import MagicMock

    v0 = MagicMock(id="v0", publishedAt=t0, uploadGapSeconds=None)
    v1 = MagicMock(id="v1", publishedAt=t1, uploadGapSeconds=None)
    v2 = MagicMock(id="v2", publishedAt=t2, uploadGapSeconds=None)

    updated = {}

    async def fake_find_many(channel_id):
        return [v0, v1, v2]

    async def fake_update(video_id, gap_seconds):
        updated[video_id] = gap_seconds

    monkeypatch.setattr(youtube_video_service, "_find_channel_videos", fake_find_many)
    monkeypatch.setattr(youtube_video_service, "_update_video_gap", fake_update)

    await youtube_video_service.update_channel_upload_gaps("chan1")

    # First video has no upload gap
    assert "v0" not in updated
    # Second video gap
    assert updated["v1"] == int((t1 - t0).total_seconds())
    # Third video gap
    assert updated["v2"] == int((t2 - t1).total_seconds())


@pytest.mark.anyio
async def test_fetch_videos_page_success(monkeypatch):
    playlist_mock = {
        "nextPageToken": "cursor_page_2",
        "items": [
            {
                "snippet": {
                    "resourceId": {"videoId": "vid_short"},
                }
            },
            {
                "snippet": {
                    "resourceId": {"videoId": "vid_long"},
                }
            },
        ],
    }

    videos_mock = {
        "items": [
            {
                "id": "vid_short",
                "snippet": {
                    "title": "Shorts Video",
                    "description": "Short",
                    "tags": ["short"],
                    "publishedAt": "2026-02-01T10:00:00Z",
                    "categoryId": "28",
                    "defaultLanguage": "en",
                },
                "statistics": {
                    "viewCount": "1000",
                    "likeCount": "100",
                    "commentCount": "10",
                },
                "contentDetails": {
                    "duration": "PT59S",
                    "definition": "hd",
                    "caption": "true",
                },
                "status": {"madeForKids": False},
            },
            {
                "id": "vid_long",
                "snippet": {
                    "title": "Long Video",
                    "description": "Long",
                    "tags": ["tutorial"],
                    "publishedAt": "2026-02-02T10:00:00Z",
                    "categoryId": "27",
                },
                "statistics": {
                    "viewCount": "5000",
                    "likeCount": "300",
                },
                "contentDetails": {
                    "duration": "PT20M",
                    "definition": "hd",
                },
                "status": {"madeForKids": False},
            },
        ]
    }

    async def fake_playlist_items(**kwargs):
        return playlist_mock

    async def fake_videos(**kwargs):
        return videos_mock

    async def fake_categories(**kwargs):
        return {
            "items": [
                {"id": "28", "snippet": {"title": "Science & Technology"}},
                {"id": "27", "snippet": {"title": "Education"}},
            ]
        }

    monkeypatch.setattr(youtube_client_service, "fetch_playlist_items", fake_playlist_items)
    monkeypatch.setattr(youtube_client_service, "fetch_videos", fake_videos)
    monkeypatch.setattr(youtube_client_service, "fetch_video_categories", fake_categories)

    saved_records = {}

    async def fake_upsert(vid_id, channel_id, record):
        saved_records[vid_id] = record
        return record

    monkeypatch.setattr(youtube_video_service, "_upsert_video", fake_upsert)
    monkeypatch.setattr(youtube_video_service, "update_channel_upload_gaps", AsyncMock())

    next_cursor, count, quota = await youtube_video_service.fetch_videos_page(
        channel_id="chan1", uploads_playlist_id="UU_test", cursor=None
    )

    assert next_cursor == "cursor_page_2"
    assert count == 2
    assert quota == 2  # 1 unit for playlistItems + 1 unit for videos.list

    assert "vid_short" in saved_records
    assert saved_records["vid_short"]["isShort"] is True
    assert saved_records["vid_short"]["categoryName"] == "Science & Technology"
    assert saved_records["vid_short"]["captionsAvailable"] is True

    assert "vid_long" in saved_records
    assert saved_records["vid_long"]["isShort"] is False
    assert saved_records["vid_long"]["categoryName"] == "Education"
