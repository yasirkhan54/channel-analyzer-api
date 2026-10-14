from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import video_fetch_controller
from routes.health_routes import client_key_header
from validators.common_validator import ErrorResponse
from validators.video_fetch_validator import FetchVideoResponse, FetchVideosResponse

router = APIRouter(tags=["Videos"], dependencies=[Security(client_key_header)])
ERRORS = {404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}}

router.add_api_route(
    "/channels/{channel_id}/videos/fetch",
    video_fetch_controller.fetch_channel_videos,
    methods=["POST"],
    response_model=FetchVideosResponse,
    responses=ERRORS,
    summary="Fetch a channel's newest N videos from YouTube with full details and store them",
    description=route_descriptions.FETCH_CHANNEL_VIDEOS,
)
router.add_api_route(
    "/videos/{video_id}/fetch",
    video_fetch_controller.fetch_video,
    methods=["POST"],
    response_model=FetchVideoResponse,
    responses=ERRORS,
    summary="Fetch one video's full details from YouTube and store it (1 unit)",
    description=route_descriptions.FETCH_VIDEO,
)
