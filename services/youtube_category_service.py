from datetime import UTC, datetime
from typing import Any

from prisma.models import VideoCategory

from configurations.database_configuration import database
from services import youtube_client_service

DEFAULT_CATEGORY_REGION = "US"
DEFAULT_CATEGORY_LANGUAGE = "en"


async def store_categories(items: list[dict[str, Any]], region_code: str, language: str) -> None:
    """Upsert videoCategories.list items; items without an ID or title are skipped."""
    now = datetime.now(UTC)
    for item in items:
        snippet = item.get("snippet", {})
        if not item.get("id") or not snippet.get("title"):
            continue
        record = {
            "title": snippet["title"],
            "assignable": bool(snippet.get("assignable", False)),
            "channelId": snippet.get("channelId"),
            "regionCode": region_code,
            "language": language,
            "fetchedAt": now,
        }
        await database.videocategory.upsert(
            where={"id": item["id"]}, data={"create": {"id": item["id"], **record}, "update": record}
        )


async def fetch_video_categories(
    region_code: str = DEFAULT_CATEGORY_REGION, language: str = DEFAULT_CATEGORY_LANGUAGE
) -> tuple[list[VideoCategory], int]:
    """Fetch YouTube's video categories for a region and store them (1 unit). Returns (categories, quota)."""
    response = await youtube_client_service.fetch_video_categories(region_code=region_code, hl=language)
    await store_categories(response.get("items", []), region_code, language)
    return await list_video_categories(), 1


async def list_video_categories() -> list[VideoCategory]:
    categories = await database.videocategory.find_many()
    return sorted(categories, key=lambda category: int(category.id) if category.id.isdigit() else 0)


async def get_stored_category_title(category_id: str) -> str | None:
    category = await database.videocategory.find_unique(where={"id": category_id})
    return category.title if category else None
