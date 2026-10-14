from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import channel_management_controller
from routes.health_routes import client_key_header
from validators.channel_read_validator import ChannelResponse
from validators.common_validator import ErrorResponse

router = APIRouter(tags=["Channel management"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/channels/{channel_id}",
    channel_management_controller.delete_channel,
    methods=["DELETE"],
    status_code=204,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Delete a channel with its videos, comments, playlists, transcripts and search results",
    description=route_descriptions.DELETE_CHANNEL,
)
router.add_api_route(
    "/channels/{channel_id}",
    channel_management_controller.update_tracking,
    methods=["PATCH"],
    response_model=ChannelResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Mark a channel tracked or untracked",
    description=route_descriptions.UPDATE_CHANNEL_TRACKING,
)
