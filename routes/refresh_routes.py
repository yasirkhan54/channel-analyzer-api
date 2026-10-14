from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import refresh_controller
from routes.health_routes import client_key_header
from validators.common_validator import ErrorResponse
from validators.refresh_validator import FullRefreshResponse, StatsRefreshResponse

router = APIRouter(tags=["Channel refresh"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/channels/{channel_id}/refresh/stats",
    refresh_controller.refresh_stats,
    methods=["POST"],
    response_model=StatsRefreshResponse,
    responses={404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Refresh a stored channel and its stored video counts",
    description=route_descriptions.REFRESH_STATS,
)
router.add_api_route(
    "/channels/{channel_id}/refresh/full",
    refresh_controller.refresh_full,
    methods=["POST"],
    response_model=FullRefreshResponse,
    status_code=201,
    responses={404: {"model": ErrorResponse}},
    summary="Queue a full refresh of a stored channel",
    description=route_descriptions.REFRESH_FULL,
)
