import re
import shlex
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from configurations.database_configuration import database
from services import youtube_client_service
from services.youtube_client_service import ResourceNotFoundError

CHANNEL_ID_REGEX = re.compile(r"^UC[\w-]{22}$")
CHANNEL_CACHE_DAYS = 30


class LegacyCustomUrlWarning(Exception):
    """Raised when resolving a legacy /c/ URL requires explicit confirmation due to 100 unit cost (FR-1.5)."""


def parse_channel_input(input_str: str) -> tuple[str, str]:
    """Parse a channel URL, @handle, or channel ID into (input_type, target_value) (FR-1.1, R-7).

    Supported formats:
    - Pure channel ID: UC... (24 chars) -> ("id", "UC...")
    - Handle: @handle -> ("handle", "handle")
    - Full URL:
      - youtube.com/channel/UC... -> ("id", "UC...")
      - youtube.com/@handle -> ("handle", "handle")
      - youtube.com/user/username -> ("username", "username")
      - youtube.com/c/custom_name -> ("legacy_c", "custom_name")
    """
    raw = input_str.strip()
    if not raw:
        raise ValueError("Channel input cannot be empty")

    # If it's a URL
    if "youtube.com" in raw or "youtu.be" in raw or raw.startswith(("http://", "https://")):
        parsed = urlparse(raw if raw.startswith(("http://", "https://")) else f"https://{raw}")
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p]

        if not parts:
            raise ValueError(f"Invalid YouTube channel URL: {input_str}")

        if parts[0] == "channel" and len(parts) >= 2:
            return "id", parts[1]
        if parts[0].startswith("@"):
            return "handle", parts[0].lstrip("@")
        if parts[0] == "user" and len(parts) >= 2:
            return "username", parts[1]
        if parts[0] == "c" and len(parts) >= 2:
            return "legacy_c", parts[1]
        if parts[0] == "c":
            raise ValueError(f"Incomplete custom URL: {input_str}")
        if len(parts) == 1 and parts[0].startswith("@"):
            return "handle", parts[0].lstrip("@")
        # Fallback single path element
        if len(parts) == 1:
            first = parts[0]
            if CHANNEL_ID_REGEX.match(first):
                return "id", first
            if first.startswith("@"):
                return "handle", first.lstrip("@")
            return "handle", first

    # Non-URL direct string
    if raw.startswith("@"):
        return "handle", raw.lstrip("@")
    if CHANNEL_ID_REGEX.match(raw):
        return "id", raw
    if raw.startswith("UC") and len(raw) == 24:
        return "id", raw

    # Default to handle
    return "handle", raw


def parse_keywords(raw: str | None) -> list[str]:
    """Parse space-separated and quoted keywords from brandingSettings.channel.keywords."""
    if not raw:
        return []
    try:
        return [kw.strip() for kw in shlex.split(raw) if kw.strip()]
    except ValueError:
        return [kw.strip() for kw in raw.split() if kw.strip()]


def _parse_channel_resource(item: dict[str, Any]) -> dict[str, Any]:
    """Extract and validate all FR-2 fields from a YouTube channels.list item."""
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})
    branding = item.get("brandingSettings", {})
    topic = item.get("topicDetails", {})

    published_str = snippet.get("publishedAt")
    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else None

    # R-8: Subscriber count rounded; empty when hidden, never 0.
    hidden_subs = stats.get("hiddenSubscriberCount", False)
    sub_count_raw = stats.get("subscriberCount")
    subscriber_count = None if hidden_subs or sub_count_raw is None else int(sub_count_raw)

    view_count = int(stats["viewCount"]) if "viewCount" in stats else None
    video_count = int(stats["videoCount"]) if "videoCount" in stats else None

    keywords = parse_keywords(branding.get("channel", {}).get("keywords"))
    topic_categories = topic.get("topicCategories", [])
    uploads_playlist_id = content.get("relatedPlaylists", {}).get("uploads")

    return {
        "id": item["id"],
        "title": snippet.get("title", ""),
        "description": snippet.get("description"),
        "customUrl": snippet.get("customUrl"),
        "country": snippet.get("country"),
        "publishedAt": published_at,
        "subscriberCount": subscriber_count,
        "subscriberCountHidden": hidden_subs,
        "viewCount": view_count,
        "videoCount": video_count,
        "keywords": keywords,
        "topicCategories": topic_categories,
        "uploadsPlaylistId": uploads_playlist_id,
        "fetchedAt": datetime.now(UTC),
    }


async def _save_channel_to_db(data: dict[str, Any]) -> Any:
    """Upsert channel into PostgreSQL using Prisma."""
    channel_id = data["id"]
    return await database.channel.upsert(
        where={"id": channel_id},
        data={
            "create": {**data, "tracked": False},
            "update": {k: v for k, v in data.items() if k != "id"},
        },
    )


async def _find_cached_channel(channel_id: str) -> Any:
    return await database.channel.find_unique(where={"id": channel_id})


async def resolve_channel_input(
    input_str: str,
    refresh: bool = False,
    confirm_legacy: bool = False,
) -> tuple[Any, int, bool]:
    """Resolve channel input using the cheapest call and return (channel, quota_spent, cached).

    Requirements:
    - FR-1.1, FR-1.2, FR-1.3, FR-1.4, FR-1.5, FR-2.1-FR-2.4, R-7, R-8.
    """
    input_type, target_val = parse_channel_input(input_str)

    # FR-1.5: Legacy /c/ warning and guard
    if input_type == "legacy_c" and not confirm_legacy:
        raise LegacyCustomUrlWarning(
            f"Resolving legacy /c/ URL '{input_str}' costs 100 quota units via search.list. "
            "Please use an @handle or channel ID instead, or provide confirm_legacy=true to proceed."
        )

    # FR-1.4: Check stored channel first if ID is known
    if input_type == "id" and not refresh:
        existing = await _find_cached_channel(target_val)
        if existing:
            age = datetime.now(UTC) - existing.fetchedAt
            if age < timedelta(days=CHANNEL_CACHE_DAYS):
                return existing, 0, True

    quota_spent = 0
    channel_id: str | None = None

    if input_type == "legacy_c":
        # Search costs 100 units (R-7)
        search_res = await youtube_client_service.fetch_search(q=target_val, type="channel", max_results=1)
        quota_spent += 100
        items = search_res.get("items", [])
        if not items:
            raise ResourceNotFoundError(f"No YouTube channel found for legacy /c/ URL: {target_val}")
        channel_id = items[0].get("id", {}).get("channelId") or items[0].get("snippet", {}).get("channelId")
        if not channel_id:
            raise ResourceNotFoundError(f"Could not resolve channel ID for: {target_val}")

        # If already cached and fresh
        if not refresh:
            existing = await _find_cached_channel(channel_id)
            if existing:
                age = datetime.now(UTC) - existing.fetchedAt
                if age < timedelta(days=CHANNEL_CACHE_DAYS):
                    return existing, quota_spent, True

        api_res = await youtube_client_service.fetch_channels(channel_id=channel_id)
        quota_spent += 1
    elif input_type == "id":
        api_res = await youtube_client_service.fetch_channels(channel_id=target_val)
        quota_spent += 1
    elif input_type == "handle":
        # Try forHandle first
        api_res = await youtube_client_service.fetch_channels(for_handle=target_val)
        quota_spent += 1
        # Fallback: if not found, try username
        if not api_res.get("items"):
            api_res = await youtube_client_service.fetch_channels(for_username=target_val)
            quota_spent += 1
    elif input_type == "username":
        api_res = await youtube_client_service.fetch_channels(for_username=target_val)
        quota_spent += 1

    items = api_res.get("items", [])
    if not items:
        raise ResourceNotFoundError(f"YouTube channel not found for input: {input_str}")

    parsed_data = _parse_channel_resource(items[0])
    saved = await _save_channel_to_db(parsed_data)
    return saved, quota_spent, False


async def fetch_channel(channel_id: str, force_refresh: bool = False) -> tuple[Any, int, bool]:
    """Fetch channel by ID, checking cache first unless force_refresh=True."""
    if not force_refresh:
        existing = await database.channel.find_unique(where={"id": channel_id})
        if existing:
            age = datetime.now(UTC) - existing.fetchedAt
            if age < timedelta(days=CHANNEL_CACHE_DAYS):
                return existing, 0, True

    api_res = await youtube_client_service.fetch_channels(channel_id=channel_id)
    items = api_res.get("items", [])
    if not items:
        raise ResourceNotFoundError(f"YouTube channel {channel_id} not found")

    parsed_data = _parse_channel_resource(items[0])
    saved = await _save_channel_to_db(parsed_data)
    return saved, 1, False


async def refresh_channel_stats(channel_id: str) -> dict[str, Any]:
    """Stats refresh of a stored channel (channel counts via channels.list) (FR-10.5)."""
    channel, _, _ = await fetch_channel(channel_id, force_refresh=True)
    return {"channel": channel, "status": "refreshed"}
