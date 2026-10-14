from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import search_controller
from routes.health_routes import client_key_header
from validators.common_validator import ErrorResponse, Page
from validators.search_validator import (
    QueueSearchResultResponse,
    SearchEstimateResponse,
    SearchQueryDetailResponse,
    SearchQueryResponse,
)

router = APIRouter(tags=["Search"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/search/estimate",
    search_controller.estimate_search,
    methods=["POST"],
    response_model=SearchEstimateResponse,
    summary="Quota cost of a search before running it (100 units per page)",
    description=route_descriptions.ESTIMATE_SEARCH,
)
router.add_api_route(
    "/search",
    search_controller.run_search,
    methods=["POST"],
    response_model=SearchQueryDetailResponse,
    status_code=201,
    responses={429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Search YouTube by keyword for videos or channels and store the results",
    description=route_descriptions.RUN_SEARCH,
)
router.add_api_route(
    "/searches",
    search_controller.list_searches,
    methods=["GET"],
    response_model=Page[SearchQueryResponse],
    summary="List stored searches, newest first",
    description=route_descriptions.LIST_SEARCHES,
)
router.add_api_route(
    "/searches/{search_id}",
    search_controller.get_search,
    methods=["GET"],
    response_model=SearchQueryDetailResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get a stored search with its results",
    description=route_descriptions.GET_SEARCH,
)
router.add_api_route(
    "/searches/{search_id}/results/{rank}/queue",
    search_controller.queue_search_result,
    methods=["POST"],
    response_model=QueueSearchResultResponse,
    status_code=201,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Queue a search result channel for a full background fetch",
    description=route_descriptions.QUEUE_SEARCH_RESULT,
)
