from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import playlist_read_controller
from routes.health_routes import client_key_header
from validators.common_validator import ErrorResponse, Page
from validators.playlist_read_validator import FetchPlaylistsResponse, PlaylistItemResponse, PlaylistResponse

router = APIRouter(tags=["Playlists"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/channels/{channel_id}/playlists/fetch",
    playlist_read_controller.fetch_channel_playlists,
    methods=["POST"],
    response_model=FetchPlaylistsResponse,
    responses={404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Fetch up to N of a channel's playlists from YouTube and store them (1 unit per 50)",
    description=route_descriptions.FETCH_CHANNEL_PLAYLISTS,
)
router.add_api_route(
    "/channels/{channel_id}/playlists",
    playlist_read_controller.list_channel_playlists,
    methods=["GET"],
    response_model=Page[PlaylistResponse],
    responses={404: {"model": ErrorResponse}},
    summary="List a channel's stored playlists",
    description=route_descriptions.LIST_CHANNEL_PLAYLISTS,
)
router.add_api_route(
    "/playlists/{playlist_id}/videos",
    playlist_read_controller.list_playlist_videos,
    methods=["GET"],
    response_model=Page[PlaylistItemResponse],
    responses={404: {"model": ErrorResponse}},
    summary="List a playlist's videos in playlist order",
    description=route_descriptions.LIST_PLAYLIST_VIDEOS,
)
