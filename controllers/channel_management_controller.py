from fastapi import HTTPException, Response

from services import channel_management_service
from services.channel_management_service import ChannelBusyError
from validators.channel_management_validator import ChannelTrackingRequest
from validators.channel_read_validator import ChannelResponse


async def delete_channel(channel_id: str) -> Response:
    try:
        deleted = await channel_management_service.delete_channel(channel_id)
    except ChannelBusyError:
        raise HTTPException(
            status_code=409, detail="Channel has a queued, running or paused fetch job; cancel it first"
        ) from None
    if not deleted:
        raise HTTPException(status_code=404, detail="Channel not found")
    return Response(status_code=204)


async def update_tracking(channel_id: str, request: ChannelTrackingRequest) -> ChannelResponse:
    channel = await channel_management_service.set_tracked(channel_id, request.tracked)
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ChannelResponse.model_validate(channel)
