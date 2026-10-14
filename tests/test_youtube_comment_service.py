import pytest

from services import youtube_client_service, youtube_comment_service


@pytest.mark.anyio
async def test_fetch_comments_skip_mode():
    next_cursor, count, quota = await youtube_comment_service.fetch_comments_page(
        video_id="vid1", mode="skip", cursor=None
    )
    assert next_cursor is None
    assert count == 0
    assert quota == 0


@pytest.mark.anyio
async def test_fetch_comments_disabled(monkeypatch):
    async def fake_fetch_threads(**kwargs):
        raise youtube_client_service.YouTubeRequestError(
            "The video identified by the <code>videoId</code> parameter has disabled comments."
        )

    monkeypatch.setattr(youtube_client_service, "fetch_comment_threads", fake_fetch_threads)

    next_cursor, count, quota = await youtube_comment_service.fetch_comments_page(
        video_id="vid_disabled", mode="top_100"
    )
    assert next_cursor is None
    assert count == 0
    assert quota == 1  # 1 unit charged by YouTube API call before finding disabled


@pytest.mark.anyio
async def test_fetch_comments_with_replies(monkeypatch):
    threads_mock = {
        "nextPageToken": "token_page_2",
        "items": [
            {
                "id": "thread1",
                "snippet": {
                    "totalReplyCount": 3,
                    "topLevelComment": {
                        "id": "c_top1",
                        "snippet": {
                            "textDisplay": "Great video!",
                            "authorDisplayName": "Viewer One",
                            "likeCount": 15,
                            "publishedAt": "2026-03-01T12:00:00Z",
                        },
                    },
                },
                "replies": {
                    "comments": [
                        {
                            "id": "c_rep1",
                            "snippet": {
                                "textDisplay": "I agree!",
                                "authorDisplayName": "Viewer Two",
                                "likeCount": 2,
                                "publishedAt": "2026-03-01T12:05:00Z",
                            },
                        }
                    ]
                },
            }
        ],
    }

    # Thread has 3 replies but only 1 returned inline => comments.list called for remaining 2
    comments_list_mock = {
        "items": [
            {
                "id": "c_rep2",
                "snippet": {
                    "textDisplay": "Me too!",
                    "authorDisplayName": "Viewer Three",
                    "likeCount": 1,
                    "publishedAt": "2026-03-01T12:10:00Z",
                },
            },
            {
                "id": "c_rep3",
                "snippet": {
                    "textDisplay": "Awesome!",
                    "authorDisplayName": "Viewer Four",
                    "likeCount": 0,
                    "publishedAt": "2026-03-01T12:15:00Z",
                },
            },
        ]
    }

    async def fake_fetch_threads(**kwargs):
        return threads_mock

    async def fake_fetch_comments(**kwargs):
        return comments_list_mock

    monkeypatch.setattr(youtube_client_service, "fetch_comment_threads", fake_fetch_threads)
    monkeypatch.setattr(youtube_client_service, "fetch_comments", fake_fetch_comments)

    saved_comments = {}

    async def fake_upsert(cid, record):
        saved_comments[cid] = record
        return record

    monkeypatch.setattr(youtube_comment_service, "_upsert_comment", fake_upsert)

    # 1. Test top_100 mode: next_cursor should be None (single page of 100)
    next_cursor, count, quota = await youtube_comment_service.fetch_comments_page(
        video_id="vid1", mode="top_100"
    )

    assert next_cursor is None
    # 1 top level + 1 inline reply + 2 extra replies = 4 total comments
    assert count == 4
    # 1 unit for threads + 1 unit for extra reply page = 2 units
    assert quota == 2

    assert "c_top1" in saved_comments
    assert saved_comments["c_top1"]["parentId"] is None
    assert saved_comments["c_top1"]["likeCount"] == 15

    assert "c_rep1" in saved_comments
    assert saved_comments["c_rep1"]["parentId"] == "c_top1"

    assert "c_rep2" in saved_comments
    assert saved_comments["c_rep2"]["parentId"] == "c_top1"


@pytest.mark.anyio
async def test_fetch_comments_all_mode_returns_cursor(monkeypatch):
    threads_mock = {
        "nextPageToken": "token_next_page",
        "items": [
            {
                "id": "thread2",
                "snippet": {
                    "totalReplyCount": 0,
                    "topLevelComment": {
                        "id": "c_top2",
                        "snippet": {
                            "textDisplay": "Nice",
                            "likeCount": 0,
                        },
                    },
                },
            }
        ],
    }

    async def fake_fetch_threads(**kwargs):
        return threads_mock

    monkeypatch.setattr(youtube_client_service, "fetch_comment_threads", fake_fetch_threads)

    async def fake_upsert(cid, record):
        return record

    monkeypatch.setattr(youtube_comment_service, "_upsert_comment", fake_upsert)

    next_cursor, count, quota = await youtube_comment_service.fetch_comments_page(
        video_id="vid1", mode="all"
    )

    assert next_cursor == "token_next_page"
    assert count == 1
    assert quota == 1
