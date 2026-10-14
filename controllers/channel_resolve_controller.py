from fastapi import HTTPException

from services import channel_service
from services.channel_service import LegacyCustomUrlWarning
from services.youtube_client_service import (
    QuotaExhaustedError,
    ResourceNotFoundError,
    YouTubeAPIError,
)
from validators.channel_read_validator import ChannelResponse
from validators.channel_resolve_validator import (
    ChannelResolveRequest,
    ChannelResolveResponse,
)


async def resolve_channel(request: ChannelResolveRequest) -> ChannelResolveResponse:
    """Resolve channel input, fetch channel details, and store in database."""
    try:
        channel, quota_spent, cached = await channel_service.resolve_channel_input(
            input_str=request.input,
            refresh=request.refresh,
            confirm_legacy=request.confirm_legacy,
        )
    except LegacyCustomUrlWarning as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QuotaExhaustedError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except YouTubeAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChannelResolveResponse(
        channel=ChannelResponse.model_validate(channel),
        quota_spent=quota_spent,
        cached=cached,
        resolved_id=channel.id,
    )
