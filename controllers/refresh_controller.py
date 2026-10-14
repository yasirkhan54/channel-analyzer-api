from fastapi import HTTPException

from services import refresh_service
from services.youtube_client_service import QuotaExhaustedError, YouTubeAPIError
from validators.channel_read_validator import ChannelResponse
from validators.refresh_validator import FullRefreshRequest, FullRefreshResponse, StatsRefreshResponse


async def refresh_stats(channel_id: str) -> StatsRefreshResponse:
    try:
        channel, videos_refreshed, quota_spent = await refresh_service.refresh_channel_stats(channel_id)
    except refresh_service.StoredChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Channel not found") from None
    except QuotaExhaustedError:
        raise HTTPException(status_code=429, detail="YouTube quota is exhausted for today") from None
    except YouTubeAPIError:
        raise HTTPException(status_code=502, detail="YouTube stats refresh request failed") from None
    return StatsRefreshResponse(
        channel=ChannelResponse.model_validate(channel),
        videos_refreshed=videos_refreshed,
        quota_spent=quota_spent,
    )


async def refresh_full(
    channel_id: str, request: FullRefreshRequest | None = None
) -> FullRefreshResponse:
    options = request or FullRefreshRequest()
    try:
        job = await refresh_service.queue_full_refresh(
            channel_id=channel_id,
            comment_mode=options.comment_mode,
            transcripts_requested=options.transcripts_requested,
        )
    except refresh_service.StoredChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Channel not found") from None
    return FullRefreshResponse(job=job)
