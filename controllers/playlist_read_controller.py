from typing import Annotated

from fastapi import HTTPException, Query

from services import channel_read_service, playlist_read_service, youtube_playlist_service
from services.youtube_client_service import QuotaExhaustedError, ResourceNotFoundError, YouTubeAPIError
from validators.channel_read_validator import VideoResponse
from validators.common_validator import Page, PageQuery
from validators.playlist_read_validator import (
    FetchPlaylistsRequest,
    FetchPlaylistsResponse,
    PlaylistItemResponse,
    PlaylistResponse,
)


async def list_channel_playlists(
    channel_id: str, query: Annotated[PageQuery, Query()]
) -> Page[PlaylistResponse]:
    if not await channel_read_service.channel_exists(channel_id):
        raise HTTPException(status_code=404, detail="Channel not found")
    playlists, total = await playlist_read_service.list_playlists(channel_id, query.skip, query.page_size)
    return Page[PlaylistResponse](
        items=[PlaylistResponse.model_validate(playlist) for playlist in playlists],
        page=query.page,
        page_size=query.page_size,
        total=total,
    )


async def list_playlist_videos(
    playlist_id: str, query: Annotated[PageQuery, Query()]
) -> Page[PlaylistItemResponse]:
    if not await playlist_read_service.playlist_exists(playlist_id):
        raise HTTPException(status_code=404, detail="Playlist not found")
    pairs, total = await playlist_read_service.list_playlist_items(playlist_id, query.skip, query.page_size)
    items = [
        PlaylistItemResponse.model_validate(item).model_copy(
            update={"video": VideoResponse.model_validate(video) if video else None}
        )
        for item, video in pairs
    ]
    return Page[PlaylistItemResponse](items=items, page=query.page, page_size=query.page_size, total=total)


async def fetch_channel_playlists(channel_id: str, request: FetchPlaylistsRequest) -> FetchPlaylistsResponse:
    try:
        result = await youtube_playlist_service.fetch_channel_playlists(
            channel_id, request.max_playlists, request.include_videos
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QuotaExhaustedError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except YouTubeAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return FetchPlaylistsResponse(
        channel_id=channel_id,
        playlists_saved=len(result.playlists),
        playlist_videos_saved=result.playlist_videos_saved,
        video_details_saved=result.video_details_saved,
        videos_from_other_channels=result.videos_from_other_channels,
        quota_spent=result.quota_spent,
        playlists=[PlaylistResponse.model_validate(playlist) for playlist in result.playlists],
    )
