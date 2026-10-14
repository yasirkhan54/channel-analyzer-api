from datetime import UTC, datetime
from typing import Any

from prisma.models import ChannelSection

from configurations.database_configuration import database
from services import channel_service, youtube_client_service


def _section_record(item: dict[str, Any], fetched_at: datetime) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    details = item.get("contentDetails", {})
    return {
        "type": snippet.get("type", ""),
        "title": snippet.get("title") or None,
        "position": int(snippet.get("position", 0)),
        "playlistIds": details.get("playlists", []),
        "channelIds": details.get("channels", []),
        "fetchedAt": fetched_at,
    }


async def channel_exists(channel_id: str) -> bool:
    return await database.channel.count(where={"id": channel_id}) > 0


async def list_sections(channel_id: str) -> list[ChannelSection]:
    return await database.channelsection.find_many(
        where={"channelId": channel_id}, order=[{"position": "asc"}, {"id": "asc"}]
    )


async def fetch_channel_sections(channel_id: str) -> tuple[list[ChannelSection], int]:
    """Fetch a channel's sections from YouTube and store them, replacing the stored list (1 unit).

    The channel is stored first when missing (1 unit). Returns (stored sections, quota_spent).
    """
    _, quota_spent, _ = await channel_service.fetch_channel(channel_id)
    response = await youtube_client_service.fetch_channel_sections(channel_id)
    quota_spent += 1
    now = datetime.now(UTC)
    items = [item for item in response.get("items", []) if item.get("id")]

    async with database.tx() as transaction:
        # Sections the owner removed since the last fetch are no longer listed, so drop them.
        await transaction.channelsection.delete_many(
            where={"channelId": channel_id, "id": {"not_in": [item["id"] for item in items]}}
        )
        for item in items:
            record = _section_record(item, now)
            await transaction.channelsection.upsert(
                where={"id": item["id"]},
                data={"create": {"id": item["id"], "channelId": channel_id, **record}, "update": record},
            )
    return await list_sections(channel_id), quota_spent
