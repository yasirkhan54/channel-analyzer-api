from fastapi import HTTPException

from controllers.video_fetch_controller import as_http_error
from services import youtube_channel_section_service
from services.youtube_client_service import YouTubeAPIError
from validators.channel_section_validator import (
    ChannelSectionListResponse,
    ChannelSectionResponse,
    FetchChannelSectionsResponse,
)


async def fetch_channel_sections(channel_id: str) -> FetchChannelSectionsResponse:
    try:
        sections, quota_spent = await youtube_channel_section_service.fetch_channel_sections(channel_id)
    except YouTubeAPIError as exc:
        raise as_http_error(exc) from exc
    return FetchChannelSectionsResponse(
        channel_id=channel_id,
        sections_saved=len(sections),
        quota_spent=quota_spent,
        sections=[ChannelSectionResponse.model_validate(section) for section in sections],
    )


async def list_channel_sections(channel_id: str) -> ChannelSectionListResponse:
    if not await youtube_channel_section_service.channel_exists(channel_id):
        raise HTTPException(status_code=404, detail="Channel not found")
    sections = await youtube_channel_section_service.list_sections(channel_id)
    return ChannelSectionListResponse(
        channel_id=channel_id,
        sections=[ChannelSectionResponse.model_validate(section) for section in sections],
    )
