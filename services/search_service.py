import html
from datetime import UTC, datetime
from typing import Any

from prisma.enums import CommentMode, FetchJobType
from prisma.models import FetchJob, SearchQuery

from configurations.database_configuration import database
from configurations.environment_configuration import get_settings
from prisma import Json
from services import fetch_job_service, quota_service, youtube_client_service
from services.youtube_client_service import QuotaExhaustedError
from validators.search_validator import SEARCH_UNIT_COST, SearchRequest


class InsufficientQuotaError(Exception):
    def __init__(self, cost: int, available: int) -> None:
        super().__init__(f"Search needs {cost} quota units but only {available} are available today")
        self.cost = cost
        self.available = available


class SearchResultNotFoundError(Exception):
    """The requested stored search result does not exist."""


class SearchResultWithoutChannelError(Exception):
    """The result cannot be associated with a channel to fetch."""


async def get_units_available() -> int:
    """Units left today above the safety margin (FR-9.3)."""
    settings = get_settings()
    spent = await quota_service.get_quota_usage()
    return max(0, settings.daily_quota_limit - settings.quota_safety_margin - spent)


def to_rfc3339(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_search_params(request: SearchRequest) -> dict[str, Any]:
    params: dict[str, Any] = {"order": request.order}
    if request.region_code:
        params["regionCode"] = request.region_code.upper()
    if request.relevance_language:
        params["relevanceLanguage"] = request.relevance_language
    if request.published_after:
        params["publishedAfter"] = to_rfc3339(request.published_after)
    if request.published_before:
        params["publishedBefore"] = to_rfc3339(request.published_before)
    return params


def parse_search_items(items: list[dict[str, Any]], first_rank: int) -> list[dict[str, Any]]:
    results = []
    for item in items:
        item_id = item.get("id", {})
        snippet = item.get("snippet", {})
        title = html.unescape(snippet["title"]) if snippet.get("title") else None
        if item_id.get("kind") == "youtube#video":
            result = {
                "resultType": "video",
                "videoId": item_id.get("videoId"),
                "channelId": snippet.get("channelId"),
            }
        elif item_id.get("kind") == "youtube#channel":
            result = {"resultType": "channel", "videoId": None, "channelId": item_id.get("channelId")}
        else:
            continue
        results.append({**result, "rank": first_rank + len(results), "title": title})
    return results


async def run_search(request: SearchRequest) -> SearchQuery:
    """Run search.list page by page (100 units each), then store the query and its results (FR-7.1 to 7.3)."""
    available = await get_units_available()
    if available < request.quota_cost:
        raise InsufficientQuotaError(request.quota_cost, available)

    params = build_search_params(request)
    results: list[dict[str, Any]] = []
    pages_run = 0
    page_token = None
    for _ in range(request.pages):
        try:
            response = await youtube_client_service.fetch_search(
                request.keyword,
                type=request.type,
                max_results=request.results_per_page,
                page_token=page_token,
                **params,
            )
        except QuotaExhaustedError:
            if pages_run == 0:
                raise
            break  # keep the pages already paid for
        pages_run += 1
        results += parse_search_items(response.get("items", []), first_rank=len(results) + 1)
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    filters = request.model_dump(mode="json", exclude={"keyword", "type"}, exclude_none=True)
    async with database.tx() as transaction:
        query = await transaction.searchquery.create(
            data={
                "keyword": request.keyword,
                "type": request.type,
                "filters": Json(filters),
                "quotaSpent": pages_run * SEARCH_UNIT_COST,
                "fetchedAt": datetime.now(UTC),
            }
        )
        if results:
            await transaction.searchresult.create_many(
                data=[{**result, "searchQueryId": query.id} for result in results]
            )
    return await get_search(query.id)


async def list_searches(skip: int, take: int) -> tuple[list[SearchQuery], int]:
    searches = await database.searchquery.find_many(
        order=[{"createdAt": "desc"}, {"id": "desc"}], skip=skip, take=take
    )
    return searches, await database.searchquery.count()


async def get_search(search_id: int) -> SearchQuery | None:
    return await database.searchquery.find_unique(
        where={"id": search_id}, include={"results": {"order_by": {"rank": "asc"}}}
    )


async def queue_search_result_for_full_fetch(
    search_id: int,
    rank: int,
    comment_mode: CommentMode,
    transcripts_requested: bool | None,
) -> FetchJob:
    """Queue the channel returned by a stored search for a full fetch (FR-7.4)."""
    result = await database.searchresult.find_unique(
        where={"searchQueryId_rank": {"searchQueryId": search_id, "rank": rank}}
    )
    if result is None:
        raise SearchResultNotFoundError
    if not result.channelId:
        raise SearchResultWithoutChannelError
    return await fetch_job_service.create_fetch_job(
        channel_input=result.channelId,
        comment_mode=comment_mode,
        job_type=FetchJobType.full_fetch,
        transcripts_requested=transcripts_requested,
    )
