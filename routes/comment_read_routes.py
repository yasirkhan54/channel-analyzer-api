from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import comment_read_controller
from routes.health_routes import client_key_header
from validators.comment_read_validator import CommentThreadResponse, FetchCommentsResponse
from validators.common_validator import ErrorResponse, Page

router = APIRouter(tags=["Comments"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/videos/{video_id}/comments/fetch",
    comment_read_controller.fetch_video_comments,
    methods=["POST"],
    response_model=FetchCommentsResponse,
    responses={404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Fetch up to N of a video's comments (with replies) from YouTube and store them (100 per unit)",
    description=route_descriptions.FETCH_VIDEO_COMMENTS,
)
router.add_api_route(
    "/videos/{video_id}/comments",
    comment_read_controller.list_video_comments,
    methods=["GET"],
    response_model=Page[CommentThreadResponse],
    responses={404: {"model": ErrorResponse}},
    summary="List a video's stored comments with their replies",
    description=route_descriptions.LIST_VIDEO_COMMENTS,
)
