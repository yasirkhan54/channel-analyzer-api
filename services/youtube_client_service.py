import logging
from typing import Any

import httpx

from configurations.environment_configuration import get_settings
from services import quota_service

YOUTUBE_V3_BASE_URL = "https://www.googleapis.com/youtube/v3"
API_KEY_HEADER = "X-Goog-Api-Key"

# httpx logs every request URL at INFO; keep it quiet so request details never reach the logs.
logging.getLogger("httpx").setLevel(logging.WARNING)


class YouTubeAPIError(Exception):
    """Base exception for YouTube Data API client errors."""


class QuotaExhaustedError(YouTubeAPIError):
    """Raised when daily quota limit or safety margin is reached, or YouTube returns quotaExceeded."""


class ResourceNotFoundError(YouTubeAPIError):
    """Raised when YouTube resource is not found (404)."""


class YouTubeServerError(YouTubeAPIError):
    """Raised on YouTube 5xx server responses."""


class YouTubeRequestError(YouTubeAPIError):
    """Raised on other YouTube API errors (bad request, network errors, etc.)."""


def _normalize_param(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list | tuple | set):
        return ",".join(str(v) for v in value)
    return str(value)


async def call_api(
    endpoint: str,
    params: dict[str, Any],
    unit_cost: int = 1,
    google_project_id: str = "default",
) -> dict[str, Any]:
    """Execute a YouTube Data API v3 call with quota safety checks and ledger tracking.

    - Refuses the call if it cuts into the configured safety margin (FR-9.3, R-16).
    - Records units in the quota ledger upon success (FR-9.1).
    - Maps errors to typed exceptions: QuotaExhaustedError, ResourceNotFoundError, YouTubeServerError.
    - Never logs or exposes the API key (R-14, FR-12.1).
    """
    is_available = await quota_service.check_quota_available(unit_cost, google_project_id=google_project_id)
    if not is_available:
        settings = get_settings()
        raise QuotaExhaustedError(
            f"Call to {endpoint} with cost {unit_cost} refused: cuts into safety margin "
            f"({settings.quota_safety_margin} units) or exceeds daily quota limit"
        )

    settings = get_settings()
    api_key = settings.youtube_api_key.get_secret_value()

    query_params: dict[str, str] = {}
    for k, v in params.items():
        val = _normalize_param(v)
        if val is not None:
            query_params[k] = val

    # The key goes in a header, never in the query string, so it cannot end up in URLs or logs.
    query_params.pop("key", None)
    headers = {API_KEY_HEADER: api_key} if api_key else {}

    url = f"{YOUTUBE_V3_BASE_URL}/{endpoint.lstrip('/')}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=query_params, headers=headers)
    except httpx.RequestError as exc:
        raise YouTubeRequestError(f"Network error connecting to YouTube API: {exc}") from exc

    if 200 <= response.status_code < 300:
        await quota_service.record_quota_spent(unit_cost, google_project_id=google_project_id)
        return response.json()

    if response.status_code == 403:
        try:
            error_data = response.json().get("error", {})
            errors = error_data.get("errors", [])
            for err in errors:
                if err.get("reason") == "quotaExceeded":
                    raise QuotaExhaustedError("YouTube API quota exceeded (quotaExceeded)")
        except (ValueError, KeyError):
            pass
        raise YouTubeRequestError(f"YouTube API returned 403 Forbidden: {response.text}")

    if response.status_code == 404:
        raise ResourceNotFoundError(f"YouTube resource not found ({endpoint})")

    if 500 <= response.status_code < 600:
        raise YouTubeServerError(f"YouTube API server error ({response.status_code})")

    raise YouTubeRequestError(
        f"YouTube API request failed with status {response.status_code}: {response.text}"
    )


async def fetch_channels(
    part: list[str] | str = "snippet,contentDetails,statistics,brandingSettings,topicDetails",
    channel_id: str | None = None,
    for_handle: str | None = None,
    for_username: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Fetch channel details via channels.list (cost: 1 unit)."""
    params: dict[str, Any] = {"part": part, **kwargs}
    if channel_id:
        params["id"] = channel_id
    if for_handle:
        params["forHandle"] = for_handle
    if for_username:
        params["forUsername"] = for_username
    return await call_api("channels", params, unit_cost=1)


async def fetch_videos(
    id: list[str] | str,
    part: list[str] | str = "snippet,contentDetails,statistics,liveStreamingDetails,status",
    **kwargs: Any,
) -> dict[str, Any]:
    """Fetch video details via videos.list in batches of up to 50 IDs (cost: 1 unit)."""
    params = {"part": part, "id": id, **kwargs}
    return await call_api("videos", params, unit_cost=1)


async def fetch_playlist_items(
    playlist_id: str,
    part: list[str] | str = "snippet,contentDetails,status",
    max_results: int = 50,
    page_token: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """List playlist items via playlistItems.list (cost: 1 unit)."""
    params: dict[str, Any] = {
        "part": part,
        "playlistId": playlist_id,
        "maxResults": max_results,
        **kwargs,
    }
    if page_token:
        params["pageToken"] = page_token
    return await call_api("playlistItems", params, unit_cost=1)


async def fetch_playlists(
    channel_id: str,
    part: list[str] | str = "snippet,contentDetails,status",
    max_results: int = 50,
    page_token: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """List channel playlists via playlists.list (cost: 1 unit)."""
    params: dict[str, Any] = {
        "part": part,
        "channelId": channel_id,
        "maxResults": max_results,
        **kwargs,
    }
    if page_token:
        params["pageToken"] = page_token
    return await call_api("playlists", params, unit_cost=1)


async def fetch_comment_threads(
    video_id: str,
    part: list[str] | str = "snippet,replies",
    order: str = "relevance",
    max_results: int = 100,
    page_token: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """List comment threads for a video via commentThreads.list (cost: 1 unit)."""
    params: dict[str, Any] = {
        "part": part,
        "videoId": video_id,
        "order": order,
        "maxResults": max_results,
        **kwargs,
    }
    if page_token:
        params["pageToken"] = page_token
    return await call_api("commentThreads", params, unit_cost=1)


async def fetch_comments(
    parent_id: str,
    part: list[str] | str = "snippet",
    max_results: int = 100,
    page_token: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """List replies to a comment via comments.list (cost: 1 unit)."""
    params: dict[str, Any] = {
        "part": part,
        "parentId": parent_id,
        "maxResults": max_results,
        **kwargs,
    }
    if page_token:
        params["pageToken"] = page_token
    return await call_api("comments", params, unit_cost=1)


async def fetch_video_categories(
    part: list[str] | str = "snippet",
    region_code: str = "US",
    **kwargs: Any,
) -> dict[str, Any]:
    """List video categories via videoCategories.list (cost: 1 unit)."""
    params = {"part": part, "regionCode": region_code, **kwargs}
    return await call_api("videoCategories", params, unit_cost=1)


async def fetch_search(
    q: str,
    part: list[str] | str = "snippet",
    type: str | None = None,
    max_results: int = 50,
    page_token: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Search YouTube via search.list (cost: 100 units)."""
    params: dict[str, Any] = {
        "part": part,
        "q": q,
        "maxResults": max_results,
        **kwargs,
    }
    if type:
        params["type"] = type
    if page_token:
        params["pageToken"] = page_token
    return await call_api("search", params, unit_cost=100)


async def fetch_captions(
    video_id: str,
    part: list[str] | str = "snippet",
    **kwargs: Any,
) -> dict[str, Any]:
    """List a video's caption tracks via captions.list (cost: 50 units). Returns track details, not text."""
    params: dict[str, Any] = {"part": part, "videoId": video_id, **kwargs}
    return await call_api("captions", params, unit_cost=50)


async def fetch_channel_sections(
    channel_id: str,
    part: list[str] | str = "snippet,contentDetails",
    **kwargs: Any,
) -> dict[str, Any]:
    """List a channel's sections (shelves) via channelSections.list (cost: 1 unit)."""
    params: dict[str, Any] = {"part": part, "channelId": channel_id, **kwargs}
    return await call_api("channelSections", params, unit_cost=1)
