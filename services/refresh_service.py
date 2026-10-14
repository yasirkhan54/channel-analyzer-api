from datetime import UTC, datetime
from itertools import batched

from prisma.enums import CommentMode, FetchJobType
from prisma.models import FetchJob

from configurations.database_configuration import database
from services import channel_service, fetch_job_service, youtube_client_service


class StoredChannelNotFoundError(Exception):
    """Raised when a refresh is requested for a channel that is not stored."""


async def _get_stored_channel(channel_id: str):
    channel = await database.channel.find_unique(where={"id": channel_id})
    if channel is None:
        raise StoredChannelNotFoundError
    return channel


async def refresh_channel_stats(channel_id: str) -> tuple[object, int, int]:
    """Refresh channel and stored video counts without discovering new videos (FR-10.5)."""
    await _get_stored_channel(channel_id)
    channel, channel_cost, _ = await channel_service.fetch_channel(channel_id, force_refresh=True)
    stored_videos = await database.video.find_many(where={"channelId": channel_id})
    refreshed = 0
    video_call_count = 0

    for video_batch in batched(stored_videos, 50):
        response = await youtube_client_service.fetch_videos(
            id=[video.id for video in video_batch], part="statistics"
        )
        video_call_count += 1
        fetched_at = datetime.now(UTC)
        for item in response.get("items", []):
            stats = item.get("statistics", {})
            await database.video.update(
                where={"id": item["id"]},
                data={
                    "viewCount": int(stats["viewCount"]) if "viewCount" in stats else None,
                    "likeCount": int(stats["likeCount"]) if "likeCount" in stats else None,
                    "commentCount": int(stats["commentCount"]) if "commentCount" in stats else None,
                    "fetchedAt": fetched_at,
                },
            )
            refreshed += 1

    return channel, refreshed, channel_cost + video_call_count


async def queue_full_refresh(
    channel_id: str,
    comment_mode: CommentMode,
    transcripts_requested: bool | None,
) -> FetchJob:
    """Queue a full refresh of an already stored channel (FR-10.6)."""
    await _get_stored_channel(channel_id)
    return await fetch_job_service.create_fetch_job(
        channel_input=channel_id,
        comment_mode=comment_mode,
        job_type=FetchJobType.full_refresh,
        transcripts_requested=transcripts_requested,
    )
