"""Swagger examples for every operation, keyed by "METHOD path" as in API_OPERATION_ORDER.

Each entry may hold a "request" body, a "response" body for the success status and "errors" for error
bodies that are not the usual {"detail": ...} shape. Path parameters get
their example from PATH_PARAMETER_EXAMPLES. tests/test_api_examples.py checks every example against the
route's real request and response models, so they cannot drift from the API.
"""

CHANNEL_ID = "UCslugpmYWJiZK5rbvtcaV7Q"
VIDEO_ID = "qT3q6T9817M"
PLAYLIST_ID = "PLLg4QQiyfp5coA3Lluo1ez7LNZLuJGZea"
FETCHED_AT = "2026-10-05T10:15:00Z"

PATH_PARAMETER_EXAMPLES = {
    "channel_id": CHANNEL_ID,
    "video_id": VIDEO_ID,
    "playlist_id": PLAYLIST_ID,
    "job_id": 1,
    "search_id": 1,
    "rank": 1,
}

CHANNEL = {
    "id": CHANNEL_ID,
    "title": "Mubasher Lucman Official",
    "description": "Mubasher Lucman is currently on the top of anchorpersons index in Pakistan & specializes "
    "in Investigative Journalism...",
    "custom_url": "@mubasherlucmanofficial",
    "country": "US",
    "published_at": "2018-04-30T11:48:26Z",
    "subscriber_count": 2430000,
    "subscriber_count_hidden": False,
    "view_count": 499424665,
    "video_count": 6525,
    "keywords": [],
    "topic_categories": [
        "https://en.wikipedia.org/wiki/Entertainment",
        "https://en.wikipedia.org/wiki/Society",
        "https://en.wikipedia.org/wiki/Television_program",
    ],
    "uploads_playlist_id": "UUslugpmYWJiZK5rbvtcaV7Q",
    "tracked": False,
    "fetched_at": FETCHED_AT,
    "created_at": FETCHED_AT,
    "updated_at": FETCHED_AT,
}

VIDEO = {
    "id": VIDEO_ID,
    "channel_id": CHANNEL_ID,
    "title": "Trouble begins for the Houthis!!! Will the Bab-el-Mandeb reopen?",
    "description": "A famous investigative current affair talk show hosted by renowned Anchorperson "
    "Mubasher Lucman.",
    "tags": ["mubasher lucman", "mubasher lucman latest", "mubasher lucman official"],
    "published_at": "2026-10-05T08:02:04Z",
    "duration_iso": "PT8M37S",
    "duration_seconds": 517,
    "is_short": False,
    "is_short_label": "heuristic",
    "upload_gap_seconds": 21600,
    "view_count": 3744,
    "like_count": 366,
    "comment_count": 17,
    "category_id": "25",
    "category_name": "News & Politics",
    "default_language": "en",
    "default_audio_language": "en-GB",
    "definition": "hd",
    "captions_available": False,
    "made_for_kids": False,
    "live_scheduled_start_at": None,
    "live_actual_start_at": None,
    "live_actual_end_at": None,
    "transcript_status": "available",
    "fetched_at": FETCHED_AT,
    "created_at": FETCHED_AT,
    "updated_at": FETCHED_AT,
}

REPLY = {
    "id": "UgxaXU2U8BoMimFCTZ14AaABAg.AQ1b2C3d4E5",
    "video_id": VIDEO_ID,
    "parent_id": "UgxaXU2U8BoMimFCTZ14AaABAg",
    "text": "Bilkul sahi farmaya",
    "author_display_name": "@example-viewer",
    "author_channel_id": "UCa1b2c3d4e5f6g7h8i9j0kl",
    "like_count": 2,
    "total_reply_count": None,
    "published_at": "2026-10-05T11:02:41Z",
    "edited_at": None,
    "fetched_at": FETCHED_AT,
}

COMMENT_THREAD = {
    "id": "UgxaXU2U8BoMimFCTZ14AaABAg",
    "video_id": VIDEO_ID,
    "parent_id": None,
    "text": "❤❤",
    "author_display_name": "@Aamir-s9r",
    "author_channel_id": "UCz9y8x7w6v5u4t3s2r1q0po",
    "like_count": 4,
    "total_reply_count": 1,
    "published_at": "2026-10-05T10:40:08Z",
    "edited_at": None,
    "fetched_at": FETCHED_AT,
    "replies": [REPLY],
}

PLAYLIST = {
    "id": PLAYLIST_ID,
    "channel_id": CHANNEL_ID,
    "title": "Motivation",
    "description": None,
    "published_at": "2025-04-08T07:27:55Z",
    "item_count": 8,
    "fetched_at": FETCHED_AT,
    "created_at": FETCHED_AT,
    "updated_at": FETCHED_AT,
}

PLAYLIST_ITEM = {
    "id": "UExMZzRRUWl5ZnA1Y29BM0xsdW8xZXo3TE5aTHVKR1plYS41NkI0NEY2RDEwNTU3Q0M2",
    "playlist_id": PLAYLIST_ID,
    "video_id": VIDEO_ID,
    "position": 0,
    "video_available": True,
    "fetched_at": FETCHED_AT,
    "video": VIDEO,
}

SEGMENT = {"position": 0, "start_seconds": 0.48, "duration_seconds": 3.2, "text": "السلام علیکم ناظرین"}

TRANSCRIPT = {
    "id": 1,
    "video_id": VIDEO_ID,
    "status": "available",
    "language_code": "ur",
    "language_name": "Urdu (auto-generated)",
    "is_generated": True,
    "full_text": "السلام علیکم ناظرین، آج ہم بات کریں گے...",
    "segment_count": 186,
    "attempt_count": 1,
    "last_error": None,
    "fetched_at": FETCHED_AT,
    "segments": [SEGMENT, {**SEGMENT, "position": 1, "start_seconds": 3.68, "text": "آج ہم بات کریں گے"}],
}

FETCH_JOB = {
    "id": 1,
    "channel_input": "@MubasherLucmanOfficial",
    "channel_id": CHANNEL_ID,
    "type": "full_fetch",
    "comment_mode": "top_100",
    "status": "running",
    "stage": "comments",
    "transcripts_requested": False,
    "transcript_step_status": "not_requested",
    "videos_found": 6525,
    "videos_done": 6525,
    "comments_fetched": 48210,
    "playlists_done": 0,
    "transcripts_done": 0,
    "transcripts_missing": 0,
    "transcripts_blocked": 0,
    "resume_cursor": {
        "stage": "comments",
        "uploads_playlist_id": "UUslugpmYWJiZK5rbvtcaV7Q",
        "comment_video_index": 1412,
        "comment_page_token": None,
    },
    "quota_spent": 1693,
    "error_detail": None,
    "started_at": "2026-10-05T10:15:02Z",
    "finished_at": None,
    "created_at": "2026-10-05T10:15:00Z",
    "updated_at": "2026-10-05T10:21:40Z",
}

QUEUED_JOB = {
    **FETCH_JOB,
    "status": "queued",
    "stage": None,
    "channel_id": None,
    "videos_found": 0,
    "videos_done": 0,
    "comments_fetched": 0,
    "resume_cursor": None,
    "quota_spent": 0,
    "started_at": None,
    "updated_at": "2026-10-05T10:15:00Z",
}

SEARCH_REQUEST = {
    "keyword": "mubasher lucman",
    "type": "video",
    "region_code": "PK",
    "relevance_language": "ur",
    "order": "relevance",
    "pages": 1,
    "results_per_page": 50,
}

SEARCH = {
    "id": 1,
    "keyword": "mubasher lucman",
    "type": "video",
    "filters": {"region_code": "PK", "relevance_language": "ur", "order": "relevance", "pages": 1},
    "quota_spent": 100,
    "fetched_at": FETCHED_AT,
    "created_at": FETCHED_AT,
}

SEARCH_DETAIL = {
    **SEARCH,
    "results": [
        {
            "rank": 1,
            "result_type": "video",
            "video_id": VIDEO_ID,
            "channel_id": CHANNEL_ID,
            "title": "Trouble begins for the Houthis!!! Will the Bab-el-Mandeb reopen?",
        },
        {
            "rank": 2,
            "result_type": "channel",
            "video_id": None,
            "channel_id": CHANNEL_ID,
            "title": "Mubasher Lucman Official",
        },
    ],
}

CAPTION_TRACK = {
    "id": "AUieDaa1b2c3d4e5f6g7h8i9j0",
    "video_id": VIDEO_ID,
    "language": "ur",
    "name": None,
    "track_kind": "asr",
    "audio_track_type": "unknown",
    "is_cc": False,
    "is_large": False,
    "is_easy_reader": False,
    "is_draft": False,
    "is_auto_synced": False,
    "status": "serving",
    "failure_reason": None,
    "last_updated": "2023-06-14T12:00:00Z",
    "fetched_at": FETCHED_AT,
}

CATEGORY = {
    "id": "25",
    "title": "News & Politics",
    "assignable": True,
    "channel_id": "UCBR8-60-B28hp2BmDPdntcQ",
    "region_code": "PK",
    "language": "en",
    "fetched_at": FETCHED_AT,
}

SECTION = {
    "id": "UCslugpmYWJiZK5rbvtcaV7Q.__WLXNpu6u8",
    "channel_id": CHANNEL_ID,
    "type": "singleplaylist",
    "title": None,
    "position": 3,
    "playlist_ids": ["PLLg4QQiyfp5dOHxiTJwg4tuXcpM3yrxTk"],
    "channel_ids": [],
    "fetched_at": FETCHED_AT,
}


def page(items: list) -> dict:
    return {"items": items, "page": 1, "page_size": 50, "total": len(items)}


OPERATION_EXAMPLES: dict[str, dict] = {
    "GET /health": {
        "response": {"status": "ok", "database": "ok"},
        "errors": {"503": {"status": "error", "database": "error"}},
    },
    "GET /quota": {
        "response": {
            "units_used": 356,
            "units_remaining": 9644,
            "safety_margin": 200,
            "daily_limit": 10000,
            "next_reset_pacific": "2026-10-06T00:00:00-07:00",
            "next_reset_pkt": "2026-10-06T12:00:00+05:00",
            "next_reset_utc": "2026-10-06T07:00:00+00:00",
            "used": 356,
            "remaining": 9644,
            "margin": 200,
        }
    },
    "POST /search/estimate": {
        "request": SEARCH_REQUEST,
        "response": {"quota_cost": 100, "units_available": 9444, "allowed": True},
    },
    "POST /search": {"request": SEARCH_REQUEST, "response": SEARCH_DETAIL},
    "GET /searches": {"response": page([SEARCH])},
    "GET /searches/{search_id}": {"response": SEARCH_DETAIL},
    "POST /searches/{search_id}/results/{rank}/queue": {
        "request": {"comment_mode": "top_100", "transcripts_requested": False},
        "response": {"job": {**QUEUED_JOB, "channel_input": CHANNEL_ID}},
    },
    "POST /channels/resolve": {
        "request": {"input": "@MubasherLucmanOfficial", "refresh": False, "confirm_legacy": False},
        "response": {"channel": CHANNEL, "quota_spent": 1, "cached": False, "resolved_id": CHANNEL_ID},
    },
    "GET /channels": {"response": page([CHANNEL])},
    "GET /channels/{channel_id}": {"response": CHANNEL},
    "POST /channels/{channel_id}/playlists/fetch": {
        "request": {"max_playlists": 50, "include_videos": True},
        "response": {
            "channel_id": CHANNEL_ID,
            "playlists_saved": 1,
            "playlist_videos_saved": 8,
            "video_details_saved": 8,
            "videos_from_other_channels": 0,
            "quota_spent": 3,
            "playlists": [PLAYLIST],
        },
    },
    "GET /channels/{channel_id}/playlists": {"response": page([PLAYLIST])},
    "GET /playlists/{playlist_id}/videos": {"response": page([PLAYLIST_ITEM])},
    "POST /channels/{channel_id}/videos/fetch": {
        "request": {"max_videos": 50, "comments_per_video": 0},
        "response": {
            "channel_id": CHANNEL_ID,
            "videos_saved": 1,
            "comments_saved": 0,
            "quota_spent": 2,
            "videos": [VIDEO],
        },
    },
    "GET /channels/{channel_id}/videos": {"response": page([VIDEO])},
    "POST /videos/{video_id}/fetch": {"response": {"quota_spent": 1, "video": VIDEO}},
    "GET /videos/{video_id}": {"response": VIDEO},
    "POST /videos/{video_id}/comments/fetch": {
        "request": {"max_comments": 100, "include_replies": True, "order": "relevance"},
        "response": {
            "video_id": VIDEO_ID,
            "comments_saved": 17,
            "replies_saved": 3,
            "comments_disabled": False,
            "quota_spent": 1,
        },
    },
    "GET /videos/{video_id}/comments": {"response": page([COMMENT_THREAD])},
    "POST /videos/{video_id}/transcript": {
        "request": {"preferred_languages": ["en", "ur", "hi"]},
        "response": TRANSCRIPT,
    },
    "GET /videos/{video_id}/transcript": {"response": TRANSCRIPT},
    "POST /channels/{channel_id}/transcripts": {
        "request": {"preferred_languages": ["en", "ur", "hi"], "only_missing": True},
        "response": {
            "channel_id": CHANNEL_ID,
            "total_videos": 6525,
            "processed": 6525,
            "available": 6102,
            "none": 419,
            "disabled": 4,
            "failed": 0,
            "blocked": 0,
            "step_status": "done",
        },
    },
    "GET /channels/{channel_id}/transcripts/status": {
        "response": page(
            [
                {
                    "video_id": VIDEO_ID,
                    "title": VIDEO["title"],
                    "transcript_status": "available",
                    "language_code": "ur",
                    "is_generated": True,
                    "attempt_count": 1,
                    "last_error": None,
                    "fetched_at": FETCHED_AT,
                }
            ]
        )
    },
    "POST /channels/{channel_id}/sections/fetch": {
        "response": {"channel_id": CHANNEL_ID, "sections_saved": 1, "quota_spent": 1, "sections": [SECTION]},
    },
    "GET /channels/{channel_id}/sections": {"response": {"channel_id": CHANNEL_ID, "sections": [SECTION]}},
    "POST /videos/{video_id}/captions/fetch": {
        "response": {
            "video_id": VIDEO_ID,
            "tracks_saved": 2,
            "quota_spent": 50,
            "tracks": [
                CAPTION_TRACK,
                {
                    **CAPTION_TRACK,
                    "id": "AUieDab9z8y7x6w5v4u3t2s1r0",
                    "language": "en",
                    "track_kind": "standard",
                },
            ],
        },
    },
    "GET /videos/{video_id}/captions": {"response": {"video_id": VIDEO_ID, "tracks": [CAPTION_TRACK]}},
    "POST /video-categories/fetch": {
        "request": {"region_code": "PK", "language": "en"},
        "response": {
            "categories_saved": 2,
            "quota_spent": 1,
            "categories": [{**CATEGORY, "id": "24", "title": "Entertainment"}, CATEGORY],
        },
    },
    "GET /video-categories": {"response": [{**CATEGORY, "id": "24", "title": "Entertainment"}, CATEGORY]},
    "POST /fetch-jobs/estimate": {
        "request": {
            "channel_input": "@MubasherLucmanOfficial",
            "comment_mode": "top_100",
            "transcripts_requested": False,
        },
        "response": {
            "channel_id": CHANNEL_ID,
            "channel_title": "Mubasher Lucman Official",
            "video_count": 6525,
            "comment_mode": "top_100",
            "estimated_quota_units_min": 6789,
            "estimated_quota_units_max": 10052,
            "transcripts_requested": False,
            "estimated_transcript_time_seconds": 0,
            "estimated_transcript_time_formatted": "0s",
            "quota_available": True,
            "current_quota_remaining": 9644,
            "warning": None,
        },
    },
    "POST /fetch-jobs": {
        "request": {
            "channel_input": "@MubasherLucmanOfficial",
            "type": "full_fetch",
            "comment_mode": "all",
            "transcripts_requested": False,
        },
        "response": {**QUEUED_JOB, "comment_mode": "all"},
    },
    "GET /fetch-jobs": {"response": page([FETCH_JOB])},
    "GET /fetch-jobs/{job_id}": {"response": FETCH_JOB},
    "POST /fetch-jobs/{job_id}/cancel": {
        "response": {**FETCH_JOB, "status": "cancelled", "updated_at": "2026-10-05T10:22:05Z"},
    },
    "POST /channels/{channel_id}/refresh/stats": {
        "response": {"channel": CHANNEL, "videos_refreshed": 6525, "quota_spent": 132},
    },
    "POST /channels/{channel_id}/refresh/full": {
        "request": {"comment_mode": "top_100", "transcripts_requested": False},
        "response": {"job": {**QUEUED_JOB, "type": "full_refresh", "channel_input": CHANNEL_ID}},
    },
    "PATCH /channels/{channel_id}": {"request": {"tracked": True}, "response": {**CHANNEL, "tracked": True}},
    "DELETE /channels/{channel_id}": {},
}

# Error bodies by status code; "{thing}" becomes Channel, Video, Playlist, Fetch job or Search from the path.
ERROR_EXAMPLES = {
    "400": "Invalid request: see the endpoint description for the accepted values",
    "404": "{thing} not found",
    "500": "Failed to create fetch job: database unavailable",
    "409": "Channel has a queued, running or paused fetch job; cancel it first",
    "422": "Search result has no channel to fetch",
    "429": "YouTube quota is exhausted for today. Quota resets at 2026-10-06T12:00:00+05:00 (PKT).",
    "502": "YouTube request failed",
    "503": "Transcript fetching blocked by YouTube: RequestBlocked",
}
