from datetime import UTC, datetime
from typing import Any

from prisma.models import CaptionTrack

from configurations.database_configuration import database
from services import youtube_client_service, youtube_video_service

CAPTIONS_UNIT_COST = 50


def parse_rfc3339_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _caption_record(snippet: dict[str, Any], fetched_at: datetime) -> dict[str, Any]:
    return {
        "language": snippet.get("language", ""),
        "name": snippet.get("name") or None,
        "trackKind": snippet.get("trackKind", "standard"),
        "audioTrackType": snippet.get("audioTrackType"),
        "isCc": snippet.get("isCC"),
        "isLarge": snippet.get("isLarge"),
        "isEasyReader": snippet.get("isEasyReader"),
        "isDraft": snippet.get("isDraft"),
        "isAutoSynced": snippet.get("isAutoSynced"),
        "status": snippet.get("status"),
        "failureReason": snippet.get("failureReason"),
        "lastUpdated": parse_rfc3339_datetime(snippet.get("lastUpdated")),
        "fetchedAt": fetched_at,
    }


async def video_exists(video_id: str) -> bool:
    return await database.video.count(where={"id": video_id}) > 0


async def list_caption_tracks(video_id: str) -> list[CaptionTrack]:
    return await database.captiontrack.find_many(
        where={"videoId": video_id}, order=[{"language": "asc"}, {"trackKind": "asc"}, {"id": "asc"}]
    )


async def fetch_video_captions(video_id: str) -> tuple[list[CaptionTrack], int]:
    """List a video's caption tracks from YouTube and store them, replacing the stored list (50 units).

    The video (and its channel) is stored first when missing. Returns (stored tracks, quota_spent).
    """
    quota_spent = 0
    if not await video_exists(video_id):
        _, quota_spent = await youtube_video_service.fetch_video(video_id)

    response = await youtube_client_service.fetch_captions(video_id)
    quota_spent += CAPTIONS_UNIT_COST
    now = datetime.now(UTC)
    items = [item for item in response.get("items", []) if item.get("id")]

    async with database.tx() as transaction:
        # Tracks the owner removed since the last fetch are no longer listed, so drop them.
        await transaction.captiontrack.delete_many(
            where={"videoId": video_id, "id": {"not_in": [item["id"] for item in items]}}
        )
        for item in items:
            record = _caption_record(item.get("snippet", {}), now)
            await transaction.captiontrack.upsert(
                where={"id": item["id"]},
                data={"create": {"id": item["id"], "videoId": video_id, **record}, "update": record},
            )
    return await list_caption_tracks(video_id), quota_spent
