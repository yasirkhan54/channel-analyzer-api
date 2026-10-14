from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import category_controller
from routes.health_routes import client_key_header
from validators.category_validator import FetchCategoriesResponse, VideoCategoryResponse
from validators.common_validator import ErrorResponse

router = APIRouter(tags=["Video categories"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/video-categories/fetch",
    category_controller.fetch_video_categories,
    methods=["POST"],
    response_model=FetchCategoriesResponse,
    responses={429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Fetch YouTube's video categories for a region and store them (1 unit)",
    description=route_descriptions.FETCH_VIDEO_CATEGORIES,
)
router.add_api_route(
    "/video-categories",
    category_controller.list_video_categories,
    methods=["GET"],
    response_model=list[VideoCategoryResponse],
    summary="List stored video categories",
    description=route_descriptions.LIST_VIDEO_CATEGORIES,
)
