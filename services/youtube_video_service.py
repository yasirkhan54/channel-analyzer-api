import contextlib
import re
from datetime import UTC, datetime
from typing import Any

from configurations.database_configuration import database
from configurations.environment_configuration import get_settings
from constants.application_constants import DEFAULT_SHORTS_THRESHOLD_SECONDS
from services import channel_service, youtube_category_service, youtube_client_service
from services.youtube_client_service import ResourceNotFoundError

_category_cache: dict[str, str] = {}


def parse_iso8601_duration(duration_iso: str | None) -> int:
    """Parse ISO 8601 duration string (e.g. PT1H2M30S) into integer seconds."""
    if not duration_iso:
        return 0
    match = re.match(r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", duration_iso)
    if not match:
        return 0
    days, hours, minutes, seconds = match.groups()
    return int(days or 0) * 86400 + int(hours or 0) * 3600 + int(minutes or 0) * 60 + int(seconds or 0)


def parse_rfc3339_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


async def get_category_name(category_id: str | None, region_code: str = "US") -> str | None:
    """Video category name by ID (FR-3.6): memory, then the stored categories, then videoCategories.list.

    The list call (1 unit) runs only when the ID is not stored yet, and its result is stored for next time.
    A failed lookup leaves the name empty and never fails the video fetch.
    """
    if not category_id:
        return None
    if category_id in _category_cache:
        return _category_cache[category_id]

    try:
        title = await youtube_category_service.get_stored_category_title(category_id)
    except Exception:
        title = None
    if title is not None:
        _category_cache[category_id] = title
        return title

    try:
        res = await youtube_client_service.fetch_video_categories(region_code=region_code)
    except Exception:
        return None
    items = res.get("items", [])
    for cat in items:
        cid = cat.get("id")
        cat_title = cat.get("snippet", {}).get("title")
        if cid and cat_title:
            _category_cache[cid] = cat_title
    # The names are already cached for this run; storing them only saves the call next time.
    with contextlib.suppress(Exception):
        await youtube_category_service.store_categories(
            items, region_code, youtube_category_service.DEFAULT_CATEGORY_LANGUAGE
        )
    return _category_cache.get(category_id)


async def _find_channel_videos(channel_id: str) -> list[Any]:
    return await database.video.find_many(
        where={"channelId": channel_id},
        order={"publishedAt": "asc"},
    )


async def _update_video_gap(video_id: str, gap_seconds: int | None) -> None:
    await database.video.update(
        where={"id": video_id},
        data={"uploadGapSeconds": gap_seconds},
    )


async def _upsert_video(vid_id: str, channel_id: str, record: dict[str, object]) -> object:
    return await database.video.upsert(
        where={"id": vid_id},
        data={
            "create": {
                "id": vid_id,
                "channelId": channel_id,
                **record,
            },
            "update": record,
        },
    )


async def update_channel_upload_gaps(channel_id: str) -> None:
    """Calculate and store upload gap seconds between consecutive videos for a channel (R-10, FR-3.3)."""
    videos = await _find_channel_videos(channel_id)
    if not videos:
        return

    # First video has no previous upload gap
    if videos[0].uploadGapSeconds is not None:
        await _update_video_gap(videos[0].id, None)

    for i in range(1, len(videos)):
        prev_pub = videos[i - 1].publishedAt
        curr_pub = videos[i].publishedAt
        gap_seconds = int((curr_pub - prev_pub).total_seconds())
        if videos[i].uploadGapSeconds != gap_seconds:
            await _update_video_gap(videos[i].id, gap_seconds)


async def _video_record(
    v: dict[str, Any], threshold: int, now: datetime
) -> tuple[str | None, dict[str, object]]:
    """Map one videos.list item to the stored FR-3 fields; returns (owner channel ID, record)."""
    v_snippet = v.get("snippet", {})
    v_stats = v.get("statistics", {})
    v_details = v.get("contentDetails", {})
    v_live = v.get("liveStreamingDetails", {})
    v_status = v.get("status", {})

    dur_iso = v_details.get("duration")
    dur_secs = parse_iso8601_duration(dur_iso)
    cat_id = v_snippet.get("categoryId")
    made_for_kids = v_status.get("madeForKids")
    if made_for_kids is None:
        made_for_kids = v_snippet.get("madeForKids")

    record: dict[str, object] = {
        "title": v_snippet.get("title", ""),
        "description": v_snippet.get("description"),
        "tags": v_snippet.get("tags", []),
        "publishedAt": parse_rfc3339_datetime(v_snippet.get("publishedAt")) or now,
        "durationIso": dur_iso,
        "durationSeconds": dur_secs,
        "isShort": dur_secs <= threshold,
        "viewCount": int(v_stats["viewCount"]) if "viewCount" in v_stats else None,
        "likeCount": int(v_stats["likeCount"]) if "likeCount" in v_stats else None,
        "commentCount": int(v_stats["commentCount"]) if "commentCount" in v_stats else None,
        "categoryId": cat_id,
        "categoryName": await get_category_name(cat_id),
        "defaultLanguage": v_snippet.get("defaultLanguage"),
        "defaultAudioLanguage": v_snippet.get("defaultAudioLanguage"),
        "definition": v_details.get("definition"),
        "captionsAvailable": v_details.get("caption") == "true" if "caption" in v_details else None,
        "madeForKids": made_for_kids,
        "liveScheduledStartAt": parse_rfc3339_datetime(v_live.get("scheduledStartTime")),
        "liveActualStartAt": parse_rfc3339_datetime(v_live.get("actualStartTime")),
        "liveActualEndAt": parse_rfc3339_datetime(v_live.get("actualEndTime")),
        "fetchedAt": now,
    }
    return v_snippet.get("channelId"), record


async def _channel_is_stored(channel_id: str) -> bool:
    return await database.channel.find_unique(where={"id": channel_id}) is not None


async def store_videos_by_id(video_ids: list[str]) -> tuple[int, int, int]:
    """Fetch full details for any video IDs (videos.list, 1 unit per 50) and store them.

    A video is stored only when its own channel is stored, since every video belongs to a stored channel;
    videos from other channels (for example in a mixed playlist) are counted and skipped.
    Returns (videos_saved, videos_from_unstored_channels, quota_spent).
    """
    threshold = getattr(get_settings(), "shorts_threshold_seconds", DEFAULT_SHORTS_THRESHOLD_SECONDS)
    unique_ids = list(dict.fromkeys(video_ids))
    stored_channels: dict[str, bool] = {}
    touched: set[str] = set()
    saved = skipped = quota_spent = 0
    now = datetime.now(UTC)

    for start in range(0, len(unique_ids), 50):
        res = await youtube_client_service.fetch_videos(id=unique_ids[start : start + 50])
        quota_spent += 1
        for v in res.get("items", []):
            owner, record = await _video_record(v, threshold, now)
            if owner and owner not in stored_channels:
                stored_channels[owner] = await _channel_is_stored(owner)
            if not owner or not stored_channels[owner]:
                skipped += 1
                continue
            await _upsert_video(v["id"], owner, record)
            touched.add(owner)
            saved += 1

    for channel_id in touched:
        await update_channel_upload_gaps(channel_id)
    return saved, skipped, quota_spent


async def fetch_videos_page(
    channel_id: str,
    uploads_playlist_id: str,
    cursor: str | None = None,
) -> tuple[str | None, int, int]:
    """Fetch one page of channel videos via uploads playlist, saving full FR-3 fields (R-4).

    Returns (next_cursor, videos_saved_count, quota_spent).
    """
    settings = get_settings()
    threshold = getattr(settings, "shorts_threshold_seconds", DEFAULT_SHORTS_THRESHOLD_SECONDS)

    # 1. List playlist items (cost 1 unit)
    playlist_res = await youtube_client_service.fetch_playlist_items(
        playlist_id=uploads_playlist_id,
        page_token=cursor,
        max_results=50,
    )
    next_cursor = playlist_res.get("nextPageToken")
    items = playlist_res.get("items", [])
    if not items:
        return next_cursor, 0, 1

    video_ids: list[str] = []
    for it in items:
        res_id = it.get("snippet", {}).get("resourceId", {}).get("videoId")
        if res_id:
            video_ids.append(res_id)

    if not video_ids:
        return next_cursor, 0, 1

    # 2. Fetch video details in batch of up to 50 (cost 1 unit)
    vids_res = await youtube_client_service.fetch_videos(id=video_ids)
    vid_items = vids_res.get("items", [])
    quota_spent = 2
    now = datetime.now(UTC)

    for v in vid_items:
        _, video_record = await _video_record(v, threshold, now)
        await _upsert_video(v["id"], channel_id, video_record)

    # Compute upload gaps across all channel videos stored so far
    await update_channel_upload_gaps(channel_id)

    return next_cursor, len(vid_items), quota_spent


async def _find_videos(video_ids: list[str]) -> list[Any]:
    return await database.video.find_many(where={"id": {"in": video_ids}}, order={"publishedAt": "desc"})


async def fetch_channel_videos(channel_id: str, max_videos: int) -> tuple[list[Any], int]:
    """Fetch a channel's newest max_videos uploads with full details, without a full fetch job.

    The channel is stored first when missing (1 unit). Listing the uploads playlist costs 1 unit per 50
    and the details 1 unit per 50. Returns (stored videos newest first, quota_spent).
    """
    channel, quota_spent, _ = await channel_service.fetch_channel(channel_id)
    if not channel.uploadsPlaylistId:
        return [], quota_spent

    video_ids: list[str] = []
    cursor: str | None = None
    while len(video_ids) < max_videos:
        remaining = max_videos - len(video_ids)
        res = await youtube_client_service.fetch_playlist_items(
            playlist_id=channel.uploadsPlaylistId,
            page_token=cursor,
            max_results=min(50, remaining),
        )
        quota_spent += 1
        for item in res.get("items", [])[:remaining]:
            video_id = item.get("snippet", {}).get("resourceId", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)
        cursor = res.get("nextPageToken")
        if not cursor:
            break

    if not video_ids:
        return [], quota_spent
    _, _, details_quota = await store_videos_by_id(video_ids)
    return await _find_videos(video_ids), quota_spent + details_quota


async def fetch_video(video_id: str) -> tuple[Any, int]:
    """Fetch one video's full details from YouTube and store it (1 unit, plus 1 if its channel is new)."""
    res = await youtube_client_service.fetch_videos(id=[video_id])
    quota_spent = 1
    items = res.get("items", [])
    if not items:
        raise ResourceNotFoundError(f"YouTube video {video_id} not found or not public")

    threshold = getattr(get_settings(), "shorts_threshold_seconds", DEFAULT_SHORTS_THRESHOLD_SECONDS)
    owner, record = await _video_record(items[0], threshold, datetime.now(UTC))
    if not owner:
        raise ResourceNotFoundError(f"YouTube video {video_id} has no channel")
    _, channel_quota, _ = await channel_service.fetch_channel(owner)
    quota_spent += channel_quota

    await _upsert_video(video_id, owner, record)
    await update_channel_upload_gaps(owner)
    videos = await _find_videos([video_id])
    return videos[0], quota_spent
