from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import channel_section_controller
from routes.health_routes import client_key_header
from validators.channel_section_validator import ChannelSectionListResponse, FetchChannelSectionsResponse
from validators.common_validator import ErrorResponse

router = APIRouter(tags=["Channel sections"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/channels/{channel_id}/sections/fetch",
    channel_section_controller.fetch_channel_sections,
    methods=["POST"],
    response_model=FetchChannelSectionsResponse,
    responses={404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Fetch a channel's sections (shelves) from YouTube and store them (1 unit)",
    description=route_descriptions.FETCH_CHANNEL_SECTIONS,
)
router.add_api_route(
    "/channels/{channel_id}/sections",
    channel_section_controller.list_channel_sections,
    methods=["GET"],
    response_model=ChannelSectionListResponse,
    responses={404: {"model": ErrorResponse}},
    summary="List a channel's stored sections in page order",
    description=route_descriptions.LIST_CHANNEL_SECTIONS,
)
