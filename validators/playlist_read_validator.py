from datetime import datetime

from pydantic import BaseModel, Field

from validators.channel_read_validator import VideoResponse
from validators.common_validator import StoredRecordResponse


class PlaylistResponse(StoredRecordResponse):
    id: str
    channel_id: str
    title: str
    description: str | None
    published_at: datetime | None
    item_count: int | None = Field(description="Video count reported by YouTube")
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime


class PlaylistItemResponse(StoredRecordResponse):
    id: str
    playlist_id: str
    video_id: str
    position: int
    video_available: bool = Field(description="False for private or deleted videos (R-17)")
    fetched_at: datetime
    video: VideoResponse | None = Field(
        None, description="The stored video, when it belongs to a stored channel; empty otherwise"
    )


class FetchPlaylistsRequest(BaseModel):
    max_playlists: int = Field(
        10, ge=1, le=500, description="How many playlists to fetch; 50 per unit of quota"
    )
    include_videos: bool = Field(
        False,
        description="Also store each playlist's videos with their full details (stats, tags, duration, "
        "category, language, captions, live details): about 2 units per 50 videos",
    )


class FetchPlaylistsResponse(BaseModel):
    channel_id: str
    playlists_saved: int
    playlist_videos_saved: int = Field(description="Playlist entries stored (video links with position)")
    video_details_saved: int = Field(description="Videos stored with full details")
    videos_from_other_channels: int = Field(
        description="Playlist videos whose channel is not stored here; their details are skipped"
    )
    quota_spent: int
    playlists: list[PlaylistResponse]
