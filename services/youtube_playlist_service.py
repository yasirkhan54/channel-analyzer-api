from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from configurations.database_configuration import database
from services import channel_service, youtube_client_service, youtube_video_service


def parse_rfc3339_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


async def _upsert_playlist(pl_id: str, channel_id: str, record: dict[str, Any]) -> Any:
    return await database.playlist.upsert(
        where={"id": pl_id},
        data={
            "create": {
                "id": pl_id,
                "channelId": channel_id,
                **record,
            },
            "update": record,
        },
    )


async def _upsert_playlist_item(item_id: str, playlist_id: str, record: dict[str, Any]) -> Any:
    return await database.playlistitem.upsert(
        where={"id": item_id},
        data={
            "create": {
                "id": item_id,
                "playlistId": playlist_id,
                **record,
            },
            "update": record,
        },
    )


def _playlist_record(pl: dict[str, Any], fetched_at: datetime) -> dict[str, Any]:
    snip = pl.get("snippet", {})
    c_details = pl.get("contentDetails", {})
    return {
        "title": snip.get("title", ""),
        "description": snip.get("description"),
        "publishedAt": parse_rfc3339_datetime(snip.get("publishedAt")),
        "itemCount": int(c_details["itemCount"]) if "itemCount" in c_details else None,
        "fetchedAt": fetched_at,
    }


async def fetch_playlist_items_page(
    playlist_id: str,
    cursor: str | None = None,
    video_ids: list[str] | None = None,
) -> tuple[str | None, int, int]:
    """Fetch one page of playlist items with position and availability (FR-5.2, R-17).

    When video_ids is given, the IDs of the available videos on the page are appended to it.

    Returns (next_cursor, items_saved_count, quota_spent).
    """
    res = await youtube_client_service.fetch_playlist_items(
        playlist_id=playlist_id,
        page_token=cursor,
        max_results=50,
    )
    next_cursor = res.get("nextPageToken")
    items = res.get("items", [])
    now = datetime.now(UTC)
    saved_count = 0

    for it in items:
        item_id = it.get("id")
        snip = it.get("snippet", {})
        res_id = snip.get("resourceId", {})
        video_id = res_id.get("videoId")
        if not item_id or not video_id:
            continue

        position = int(snip.get("position", 0))
        title = snip.get("title", "")
        status = it.get("status", {})
        privacy = status.get("privacyStatus")

        # R-17: Record private/deleted videos as unavailable
        video_available = privacy != "private" and title not in ("Private video", "Deleted video")

        item_record = {
            "videoId": video_id,
            "position": position,
            "videoAvailable": video_available,
            "fetchedAt": now,
        }

        await _upsert_playlist_item(item_id, playlist_id, item_record)
        saved_count += 1
        if video_ids is not None and video_available:
            video_ids.append(video_id)

    return next_cursor, saved_count, 1


async def fetch_all_playlist_items(playlist_id: str) -> tuple[int, int]:
    """Fetch all items for a playlist across pages."""
    cursor: str | None = None
    total_saved = 0
    total_quota = 0

    while True:
        cursor, count, quota = await fetch_playlist_items_page(playlist_id, cursor=cursor)
        total_saved += count
        total_quota += quota
        if not cursor:
            break

    return total_saved, total_quota


async def fetch_playlists_page(
    channel_id: str,
    cursor: str | None = None,
    fetch_items: bool = True,
) -> tuple[str | None, int, int]:
    """Fetch one page of playlists for a channel, and optionally their items (FR-5.1, FR-5.2).

    Returns (next_cursor, playlists_saved_count, quota_spent).
    """
    res = await youtube_client_service.fetch_playlists(
        channel_id=channel_id,
        page_token=cursor,
        max_results=50,
    )
    next_cursor = res.get("nextPageToken")
    items = res.get("items", [])
    now = datetime.now(UTC)
    quota_spent = 1  # 1 unit for playlists.list

    for pl in items:
        pl_id = pl.get("id")
        if not pl_id:
            continue
        await _upsert_playlist(pl_id, channel_id, _playlist_record(pl, now))

        if fetch_items:
            _, item_quota = await fetch_all_playlist_items(pl_id)
            quota_spent += item_quota

    return next_cursor, len(items), quota_spent


@dataclass
class PlaylistFetchResult:
    playlists: list[Any] = field(default_factory=list)
    playlist_videos_saved: int = 0
    video_details_saved: int = 0
    videos_from_other_channels: int = 0
    quota_spent: int = 0


async def fetch_playlist_videos_with_details(playlist_id: str) -> tuple[int, int, int, int]:
    """Store every item of a playlist plus each video's full details (2 units per 50 videos).

    Returns (items_saved, video_details_saved, videos_from_other_channels, quota_spent).
    """
    cursor: str | None = None
    items_saved = details_saved = skipped = quota_spent = 0
    while True:
        page_ids: list[str] = []
        cursor, count, quota = await fetch_playlist_items_page(playlist_id, cursor=cursor, video_ids=page_ids)
        items_saved += count
        quota_spent += quota
        if page_ids:
            saved, other, video_quota = await youtube_video_service.store_videos_by_id(page_ids)
            details_saved += saved
            skipped += other
            quota_spent += video_quota
        if not cursor:
            break
    return items_saved, details_saved, skipped, quota_spent


async def fetch_channel_playlists(
    channel_id: str,
    max_playlists: int,
    include_videos: bool = False,
) -> PlaylistFetchResult:
    """Fetch up to max_playlists of a channel's playlists without a full fetch job.

    The channel is stored first when missing (1 unit). Each playlists.list page of up to 50 costs 1 unit.
    With include_videos, every playlist's videos are stored with their full details:
    1 unit per 50 playlist items plus 1 unit per 50 videos.
    """
    result = PlaylistFetchResult()
    _, result.quota_spent, _ = await channel_service.fetch_channel(channel_id)
    cursor: str | None = None
    now = datetime.now(UTC)

    while len(result.playlists) < max_playlists:
        remaining = max_playlists - len(result.playlists)
        res = await youtube_client_service.fetch_playlists(
            channel_id=channel_id,
            page_token=cursor,
            max_results=min(50, remaining),
        )
        result.quota_spent += 1
        for pl in res.get("items", [])[:remaining]:
            pl_id = pl.get("id")
            if pl_id:
                result.playlists.append(await _upsert_playlist(pl_id, channel_id, _playlist_record(pl, now)))
        cursor = res.get("nextPageToken")
        if not cursor:
            break

    if include_videos:
        for playlist in result.playlists:
            items, details, other, quota = await fetch_playlist_videos_with_details(playlist.id)
            result.playlist_videos_saved += items
            result.video_details_saved += details
            result.videos_from_other_channels += other
            result.quota_spent += quota

    return result
