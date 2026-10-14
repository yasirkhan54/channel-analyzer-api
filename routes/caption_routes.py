from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import caption_controller
from routes.health_routes import client_key_header
from validators.caption_validator import CaptionTrackListResponse, FetchCaptionsResponse
from validators.common_validator import ErrorResponse

router = APIRouter(tags=["Captions"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/videos/{video_id}/captions/fetch",
    caption_controller.fetch_video_captions,
    methods=["POST"],
    response_model=FetchCaptionsResponse,
    responses={404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Fetch a video's caption track list from YouTube and store it (50 units)",
    description=route_descriptions.FETCH_VIDEO_CAPTIONS,
)
router.add_api_route(
    "/videos/{video_id}/captions",
    caption_controller.list_video_captions,
    methods=["GET"],
    response_model=CaptionTrackListResponse,
    responses={404: {"model": ErrorResponse}},
    summary="List a video's stored caption tracks",
    description=route_descriptions.LIST_VIDEO_CAPTIONS,
)
