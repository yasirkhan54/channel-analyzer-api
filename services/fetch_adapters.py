import math
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from configurations.database_configuration import database
from constants.application_constants import DEFAULT_SHORTS_THRESHOLD_SECONDS
from services import youtube_client_service


def parse_iso8601_duration(duration_iso: str | None) -> int:
    """Parses ISO 8601 duration format (e.g. PT1H2M30S) into integer seconds."""
    if not duration_iso:
        return 0
    match = re.match(
        r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$",
        duration_iso,
    )
    if not match:
        return 0
    days, hours, minutes, seconds = match.groups()
    return (
        int(days or 0) * 86400
        + int(hours or 0) * 3600
        + int(minutes or 0) * 60
        + int(seconds or 0)
    )


def parse_rfc3339_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def extract_channel_query(channel_input: str) -> dict[str, str]:
    """Parses a channel URL, handle, or ID into API query parameters."""
    raw = channel_input.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        path = parsed.path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == "channel":
            return {"channel_id": parts[1]}
        if len(parts) >= 1 and parts[0].startswith("@"):
            return {"for_handle": parts[0]}
        if len(parts) >= 2 and parts[0] == "user":
            return {"for_username": parts[1]}
        if len(parts) >= 2 and parts[0] == "c":
            return {"for_custom_url": parts[1]}
        if len(parts) == 1 and parts[0]:
            if parts[0].startswith("@"):
                return {"for_handle": parts[0]}
            if parts[0].startswith("UC"):
                return {"channel_id": parts[0]}
            return {"for_handle": f"@{parts[0]}"}

    if raw.startswith("@"):
        return {"for_handle": raw}
    if raw.startswith("UC") and len(raw) >= 20:
        return {"channel_id": raw}
    return {"for_handle": f"@{raw}" if not raw.startswith("@") else raw}


async def resolve_and_fetch_channel(
    channel_input: str,
    confirm_legacy: bool = False,
) -> dict[str, Any]:
    """Resolves channel input and stores the channel record (FR-1.1 to FR-1.5)."""
    try:
        from services import channel_service

        if hasattr(channel_service, "resolve_channel_input"):
            resolved = await channel_service.resolve_channel_input(
                channel_input,
                confirm_legacy=confirm_legacy,
            )
            chan_obj = resolved[0] if isinstance(resolved, tuple) else resolved
            if hasattr(chan_obj, "id"):
                return {
                    "id": chan_obj.id,
                    "title": chan_obj.title,
                    "uploads_playlist_id": getattr(chan_obj, "uploadsPlaylistId", None),
                    "video_count": getattr(chan_obj, "videoCount", 0) or 0,
                    "channel": chan_obj,
                }
            if isinstance(chan_obj, dict):
                return {
                    "id": chan_obj.get("id"),
                    "title": chan_obj.get("title"),
                    "uploads_playlist_id": (
                        chan_obj.get("uploads_playlist_id") or chan_obj.get("uploadsPlaylistId")
                    ),
                    "video_count": chan_obj.get("video_count") or chan_obj.get("videoCount", 0),
                    "channel": chan_obj,
                }
    except Exception:
        pass

    q = extract_channel_query(channel_input)
    if "for_custom_url" in q:
        if not confirm_legacy:
            raise ValueError(
                "Resolving legacy /c/ URLs costs 100 quota units via search. "
                "Confirm legacy resolution or provide an @handle or channel ID."
            )
        search_res = await youtube_client_service.fetch_search(
            q=q["for_custom_url"],
            type="channel",
            max_results=1,
        )
        items = search_res.get("items", [])
        if not items:
            raise ValueError(f"Could not resolve channel: {channel_input}")
        q = {"channel_id": items[0]["snippet"]["channelId"]}

    res = await youtube_client_service.fetch_channels(
        channel_id=q.get("channel_id"),
        for_handle=q.get("for_handle"),
        for_username=q.get("for_username"),
    )
    items = res.get("items", [])
    if not items:
        raise ValueError(f"Channel not found for input: {channel_input}")

    item = items[0]
    chan_id = item["id"]
    snippet = item.get("snippet", {})
    statistics = item.get("statistics", {})
    branding = item.get("brandingSettings", {}).get("channel", {})
    topic_details = item.get("topicDetails", {})
    related_playlists = item.get("contentDetails", {}).get("relatedPlaylists", {})
    uploads_id = related_playlists.get("uploads")

    raw_keywords = branding.get("keywords", "")
    keywords = [k.strip('"').strip() for k in raw_keywords.split()] if raw_keywords else []
    topics = topic_details.get("topicCategories", [])

    subs_hidden = statistics.get("hiddenSubscriberCount", False)
    subs = None if subs_hidden else int(statistics.get("subscriberCount", 0))

    now = datetime.now(UTC)
    channel = await database.channel.upsert(
        where={"id": chan_id},
        data={
            "create": {
                "id": chan_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description"),
                "customUrl": snippet.get("customUrl"),
                "country": snippet.get("country"),
                "publishedAt": parse_rfc3339_datetime(snippet.get("publishedAt")),
                "subscriberCount": subs,
                "subscriberCountHidden": subs_hidden,
                "viewCount": int(statistics.get("viewCount", 0)),
                "videoCount": int(statistics.get("videoCount", 0)),
                "keywords": keywords,
                "topicCategories": topics,
                "uploadsPlaylistId": uploads_id,
                "tracked": False,
                "fetchedAt": now,
            },
            "update": {
                "title": snippet.get("title", ""),
                "description": snippet.get("description"),
                "customUrl": snippet.get("customUrl"),
                "country": snippet.get("country"),
                "subscriberCount": subs,
                "subscriberCountHidden": subs_hidden,
                "viewCount": int(statistics.get("viewCount", 0)),
                "videoCount": int(statistics.get("videoCount", 0)),
                "keywords": keywords,
                "topicCategories": topics,
                "uploadsPlaylistId": uploads_id,
                "fetchedAt": now,
            },
        },
    )

    return {
        "id": channel.id,
        "title": channel.title,
        "uploads_playlist_id": uploads_id,
        "video_count": channel.videoCount or 0,
        "channel": channel,
    }


async def fetch_videos_page(
    channel_id: str,
    uploads_playlist_id: str,
    cursor: str | None = None,
) -> tuple[str | None, int, int]:
    """Fetches one page of channel videos via uploads playlist (R-4, FR-3.1 to FR-3.7)."""
    try:
        from services import youtube_video_service

        if hasattr(youtube_video_service, "fetch_videos_page"):
            return await youtube_video_service.fetch_videos_page(channel_id, uploads_playlist_id, cursor)
    except ImportError:
        pass

    playlist_res = await youtube_client_service.fetch_playlist_items(
        playlist_id=uploads_playlist_id,
        page_token=cursor,
        max_results=50,
    )
    next_cursor = playlist_res.get("nextPageToken")
    items = playlist_res.get("items", [])
    if not items:
        return None, 0, 1

    video_ids = [
        it["snippet"]["resourceId"]["videoId"]
        for it in items
        if "snippet" in it and "resourceId" in it["snippet"] and "videoId" in it["snippet"]["resourceId"]
    ]
    if not video_ids:
        return next_cursor, 0, 1

    vids_res = await youtube_client_service.fetch_videos(id=video_ids)
    vid_items = vids_res.get("items", [])

    now = datetime.now(UTC)
    for v in vid_items:
        vid_id = v["id"]
        v_snippet = v.get("snippet", {})
        v_stats = v.get("statistics", {})
        v_details = v.get("contentDetails", {})
        v_live = v.get("liveStreamingDetails", {})

        dur_iso = v_details.get("duration")
        dur_secs = parse_iso8601_duration(dur_iso)
        is_short = dur_secs <= DEFAULT_SHORTS_THRESHOLD_SECONDS

        pub_at = parse_rfc3339_datetime(v_snippet.get("publishedAt")) or now
        view_cnt = int(v_stats.get("viewCount", 0)) if "viewCount" in v_stats else None
        like_cnt = int(v_stats.get("likeCount", 0)) if "likeCount" in v_stats else None
        comment_cnt = int(v_stats.get("commentCount", 0)) if "commentCount" in v_stats else None

        await database.video.upsert(
            where={"id": vid_id},
            data={
                "create": {
                    "id": vid_id,
                    "channelId": channel_id,
                    "title": v_snippet.get("title", ""),
                    "description": v_snippet.get("description"),
                    "tags": v_snippet.get("tags", []),
                    "publishedAt": pub_at,
                    "durationIso": dur_iso,
                    "durationSeconds": dur_secs,
                    "isShort": is_short,
                    "viewCount": view_cnt,
                    "likeCount": like_cnt,
                    "commentCount": comment_cnt,
                    "categoryId": v_snippet.get("categoryId"),
                    "defaultLanguage": v_snippet.get("defaultLanguage"),
                    "defaultAudioLanguage": v_snippet.get("defaultAudioLanguage"),
                    "definition": v_details.get("definition"),
                    "captionsAvailable": v_details.get("caption") == "true",
                    "liveScheduledStartAt": parse_rfc3339_datetime(v_live.get("scheduledStartTime")),
                    "liveActualStartAt": parse_rfc3339_datetime(v_live.get("actualStartTime")),
                    "liveActualEndAt": parse_rfc3339_datetime(v_live.get("actualEndTime")),
                    "fetchedAt": now,
                },
                "update": {
                    "title": v_snippet.get("title", ""),
                    "description": v_snippet.get("description"),
                    "tags": v_snippet.get("tags", []),
                    "durationIso": dur_iso,
                    "durationSeconds": dur_secs,
                    "isShort": is_short,
                    "viewCount": view_cnt,
                    "likeCount": like_cnt,
                    "commentCount": comment_cnt,
                    "categoryId": v_snippet.get("categoryId"),
                    "defaultLanguage": v_snippet.get("defaultLanguage"),
                    "defaultAudioLanguage": v_snippet.get("defaultAudioLanguage"),
                    "definition": v_details.get("definition"),
                    "captionsAvailable": v_details.get("caption") == "true",
                    "liveScheduledStartAt": parse_rfc3339_datetime(v_live.get("scheduledStartTime")),
                    "liveActualStartAt": parse_rfc3339_datetime(v_live.get("actualStartTime")),
                    "liveActualEndAt": parse_rfc3339_datetime(v_live.get("actualEndTime")),
                    "fetchedAt": now,
                },
            },
        )

    # 1 unit for playlistItems + 1 unit for videos.list = 2 units
    return next_cursor, len(vid_items), 2


async def fetch_comments_page(
    video_id: str,
    mode: str,
    cursor: str | None = None,
) -> tuple[str | None, int, int]:
    """Fetches one page of comments and replies for a video (R-5, R-23, FR-4.1)."""
    try:
        from services import youtube_comment_service

        if hasattr(youtube_comment_service, "fetch_comments_page"):
            return await youtube_comment_service.fetch_comments_page(video_id, mode, cursor)
    except ImportError:
        pass

    try:
        threads_res = await youtube_client_service.fetch_comment_threads(
            video_id=video_id,
            order="relevance",
            max_results=100,
            page_token=cursor,
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "disabled" in msg or "commentsdisabled" in msg:
            return None, 0, 1
        raise

    next_cursor = threads_res.get("nextPageToken")
    items = threads_res.get("items", [])
    now = datetime.now(UTC)
    total_comments_saved = 0
    quota_spent = 1

    for it in items:
        top = it.get("snippet", {}).get("topLevelComment", {})
        top_snippet = top.get("snippet", {})
        comment_id = top.get("id")
        if not comment_id:
            continue

        await database.comment.upsert(
            where={"id": comment_id},
            data={
                "create": {
                    "id": comment_id,
                    "videoId": video_id,
                    "text": top_snippet.get("textDisplay", ""),
                    "authorDisplayName": top_snippet.get("authorDisplayName"),
                    "authorChannelId": top_snippet.get("authorChannelId", {}).get("value")
                    if isinstance(top_snippet.get("authorChannelId"), dict)
                    else None,
                    "likeCount": int(top_snippet.get("likeCount", 0)),
                    "totalReplyCount": int(it.get("snippet", {}).get("totalReplyCount", 0)),
                    "publishedAt": parse_rfc3339_datetime(top_snippet.get("publishedAt")) or now,
                    "editedAt": parse_rfc3339_datetime(top_snippet.get("updatedAt")),
                    "fetchedAt": now,
                },
                "update": {
                    "text": top_snippet.get("textDisplay", ""),
                    "authorDisplayName": top_snippet.get("authorDisplayName"),
                    "likeCount": int(top_snippet.get("likeCount", 0)),
                    "totalReplyCount": int(it.get("snippet", {}).get("totalReplyCount", 0)),
                    "editedAt": parse_rfc3339_datetime(top_snippet.get("updatedAt")),
                    "fetchedAt": now,
                },
            },
        )
        total_comments_saved += 1

        replies = it.get("replies", {}).get("comments", [])
        for rep in replies:
            rep_id = rep.get("id")
            rep_snip = rep.get("snippet", {})
            if rep_id:
                await database.comment.upsert(
                    where={"id": rep_id},
                    data={
                        "create": {
                            "id": rep_id,
                            "videoId": video_id,
                            "parentId": comment_id,
                            "text": rep_snip.get("textDisplay", ""),
                            "authorDisplayName": rep_snip.get("authorDisplayName"),
                            "authorChannelId": rep_snip.get("authorChannelId", {}).get("value")
                            if isinstance(rep_snip.get("authorChannelId"), dict)
                            else None,
                            "likeCount": int(rep_snip.get("likeCount", 0)),
                            "publishedAt": parse_rfc3339_datetime(rep_snip.get("publishedAt")) or now,
                            "editedAt": parse_rfc3339_datetime(rep_snip.get("updatedAt")),
                            "fetchedAt": now,
                        },
                        "update": {
                            "text": rep_snip.get("textDisplay", ""),
                            "authorDisplayName": rep_snip.get("authorDisplayName"),
                            "likeCount": int(rep_snip.get("likeCount", 0)),
                            "editedAt": parse_rfc3339_datetime(rep_snip.get("updatedAt")),
                            "fetchedAt": now,
                        },
                    },
                )
                total_comments_saved += 1

    return next_cursor, total_comments_saved, quota_spent


async def fetch_playlists_page(
    channel_id: str,
    cursor: str | None = None,
) -> tuple[str | None, int, int]:
    """Fetches one page of playlists for a channel (FR-5.1)."""
    try:
        from services import youtube_playlist_service

        if hasattr(youtube_playlist_service, "fetch_playlists_page"):
            return await youtube_playlist_service.fetch_playlists_page(channel_id, cursor)
    except ImportError:
        pass

    res = await youtube_client_service.fetch_playlists(
        channel_id=channel_id,
        page_token=cursor,
        max_results=50,
    )
    next_cursor = res.get("nextPageToken")
    items = res.get("items", [])
    now = datetime.now(UTC)

    for pl in items:
        pl_id = pl["id"]
        snip = pl.get("snippet", {})
        c_details = pl.get("contentDetails", {})
        item_count = int(c_details.get("itemCount", 0))

        await database.playlist.upsert(
            where={"id": pl_id},
            data={
                "create": {
                    "id": pl_id,
                    "channelId": channel_id,
                    "title": snip.get("title", ""),
                    "description": snip.get("description"),
                    "publishedAt": parse_rfc3339_datetime(snip.get("publishedAt")),
                    "itemCount": item_count,
                    "fetchedAt": now,
                },
                "update": {
                    "title": snip.get("title", ""),
                    "description": snip.get("description"),
                    "itemCount": item_count,
                    "fetchedAt": now,
                },
            },
        )

    return next_cursor, len(items), 1


def calculate_job_estimate(
    video_count: int,
    comment_mode: str,
    transcripts_requested: bool,
    pause_seconds: float = 2.0,
) -> dict[str, Any]:
    """Computes quota cost and transcript time estimates (FR-8.8, FR-6.11)."""
    # 1 for channel
    base_channel = 1
    # 1 for playlistItems (50/page) + 1 for videos.list (50/batch) = 2 per 50 videos
    video_batches = math.ceil(video_count / 50) if video_count > 0 else 1
    video_units = video_batches * 2
    playlist_units = 1  # estimate for channel playlists

    if comment_mode == "skip":
        comment_min = 0
        comment_max = 0
    elif comment_mode == "top_100":
        # ~1 unit per video for 100 comment threads, plus potential reply pages
        comment_min = video_count
        comment_max = math.ceil(video_count * 1.5)
    else:  # "all"
        # range because comment volume per video is unknown prior to fetching
        comment_min = video_count
        comment_max = max(video_count * 5, 100)

    est_min = base_channel + video_units + playlist_units + comment_min
    est_max = base_channel + video_units + playlist_units + comment_max

    transcript_time = int(video_count * pause_seconds) if transcripts_requested else 0
    mins = transcript_time // 60
    secs = transcript_time % 60
    formatted_time = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

    return {
        "video_count": video_count,
        "estimated_quota_units_min": est_min,
        "estimated_quota_units_max": est_max,
        "transcripts_requested": transcripts_requested,
        "estimated_transcript_time_seconds": transcript_time,
        "estimated_transcript_time_formatted": formatted_time,
    }
