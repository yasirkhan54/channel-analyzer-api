from fastapi import APIRouter, Security
from fastapi.security import APIKeyHeader

from constants import route_descriptions
from constants.application_constants import CLIENT_KEY_HEADER
from controllers import channel_resolve_controller
from validators.channel_resolve_validator import ChannelResolveResponse

client_key_header = APIKeyHeader(name=CLIENT_KEY_HEADER, auto_error=False)

router = APIRouter(tags=["Find channel"])

router.add_api_route(
    "/channels/resolve",
    channel_resolve_controller.resolve_channel,
    methods=["POST"],
    response_model=ChannelResolveResponse,
    dependencies=[Security(client_key_header)],
    summary="Resolve channel URL, @handle, or ID and store details (FR-1, FR-2)",
    description=route_descriptions.RESOLVE_CHANNEL,
)
