from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import channel_read_controller
from routes.health_routes import client_key_header
from validators.channel_read_validator import ChannelResponse, VideoResponse
from validators.common_validator import ErrorResponse, Page

router = APIRouter(dependencies=[Security(client_key_header)])

router.add_api_route(
    "/channels",
    channel_read_controller.list_channels,
    methods=["GET"],
    response_model=Page[ChannelResponse],
    tags=["Channels"],
    summary="List stored channels",
    description=route_descriptions.LIST_CHANNELS,
)
router.add_api_route(
    "/channels/{channel_id}",
    channel_read_controller.get_channel,
    methods=["GET"],
    response_model=ChannelResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["Channels"],
    summary="Get a stored channel",
    description=route_descriptions.GET_CHANNEL,
)
router.add_api_route(
    "/channels/{channel_id}/videos",
    channel_read_controller.list_channel_videos,
    methods=["GET"],
    response_model=Page[VideoResponse],
    responses={404: {"model": ErrorResponse}},
    tags=["Videos"],
    summary="List a channel's stored videos",
    description=route_descriptions.LIST_CHANNEL_VIDEOS,
)
router.add_api_route(
    "/videos/{video_id}",
    channel_read_controller.get_video,
    methods=["GET"],
    response_model=VideoResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["Videos"],
    summary="Get a stored video",
    description=route_descriptions.GET_VIDEO,
)
