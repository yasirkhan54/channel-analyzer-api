from typing import Annotated

from fastapi import HTTPException, Query

from services import channel_read_service
from validators.channel_read_validator import ChannelResponse, VideoListQuery, VideoResponse
from validators.common_validator import Page, PageQuery


async def list_channels(query: Annotated[PageQuery, Query()]) -> Page[ChannelResponse]:
    channels, total = await channel_read_service.list_channels(query.skip, query.page_size)
    return Page[ChannelResponse](
        items=[ChannelResponse.model_validate(channel) for channel in channels],
        page=query.page,
        page_size=query.page_size,
        total=total,
    )


async def get_channel(channel_id: str) -> ChannelResponse:
    channel = await channel_read_service.get_channel(channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ChannelResponse.model_validate(channel)


async def list_channel_videos(
    channel_id: str, query: Annotated[VideoListQuery, Query()]
) -> Page[VideoResponse]:
    if not await channel_read_service.channel_exists(channel_id):
        raise HTTPException(status_code=404, detail="Channel not found")
    videos, total = await channel_read_service.list_videos(channel_id, query)
    return Page[VideoResponse](
        items=[VideoResponse.model_validate(video) for video in videos],
        page=query.page,
        page_size=query.page_size,
        total=total,
    )


async def get_video(video_id: str) -> VideoResponse:
    video = await channel_read_service.get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoResponse.model_validate(video)
