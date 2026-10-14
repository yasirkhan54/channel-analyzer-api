from typing import Annotated

from fastapi import HTTPException, Query

from services import quota_service, search_service
from services.search_service import InsufficientQuotaError
from services.youtube_client_service import QuotaExhaustedError, YouTubeAPIError
from validators.common_validator import Page, PageQuery
from validators.search_validator import (
    QueueSearchResultRequest,
    QueueSearchResultResponse,
    SearchEstimateResponse,
    SearchQueryDetailResponse,
    SearchQueryResponse,
    SearchRequest,
)


def quota_refused(message: str) -> HTTPException:
    _, reset_pkt, _ = quota_service.get_next_reset_times()
    return HTTPException(status_code=429, detail=f"{message}. Quota resets at {reset_pkt.isoformat()} (PKT).")


async def estimate_search(request: SearchRequest) -> SearchEstimateResponse:
    available = await search_service.get_units_available()
    return SearchEstimateResponse(
        quota_cost=request.quota_cost, units_available=available, allowed=available >= request.quota_cost
    )


async def run_search(request: SearchRequest) -> SearchQueryDetailResponse:
    try:
        search = await search_service.run_search(request)
    except InsufficientQuotaError as error:
        raise quota_refused(str(error)) from None
    except QuotaExhaustedError:
        raise quota_refused("YouTube quota is exhausted for today") from None
    except YouTubeAPIError:
        # The client error text can echo the request; keep it out of the response (R-14).
        raise HTTPException(status_code=502, detail="YouTube search request failed") from None
    return SearchQueryDetailResponse.model_validate(search)


async def list_searches(query: Annotated[PageQuery, Query()]) -> Page[SearchQueryResponse]:
    searches, total = await search_service.list_searches(query.skip, query.page_size)
    return Page[SearchQueryResponse](
        items=[SearchQueryResponse.model_validate(search) for search in searches],
        page=query.page,
        page_size=query.page_size,
        total=total,
    )


async def get_search(search_id: int) -> SearchQueryDetailResponse:
    search = await search_service.get_search(search_id)
    if search is None:
        raise HTTPException(status_code=404, detail="Search not found")
    return SearchQueryDetailResponse.model_validate(search)


async def queue_search_result(
    search_id: int,
    rank: int,
    request: QueueSearchResultRequest | None = None,
) -> QueueSearchResultResponse:
    options = request or QueueSearchResultRequest()
    try:
        job = await search_service.queue_search_result_for_full_fetch(
            search_id=search_id,
            rank=rank,
            comment_mode=options.comment_mode,
            transcripts_requested=options.transcripts_requested,
        )
    except search_service.SearchResultNotFoundError:
        raise HTTPException(status_code=404, detail="Search result not found") from None
    except search_service.SearchResultWithoutChannelError:
        raise HTTPException(status_code=422, detail="Search result has no channel to fetch") from None
    return QueueSearchResultResponse(job=job)
