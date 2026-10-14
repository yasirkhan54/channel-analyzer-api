from pydantic import BaseModel, Field

from validators.channel_read_validator import VideoResponse


class FetchVideosRequest(BaseModel):
    max_videos: int = Field(
        50, ge=1, le=500, description="How many of the newest uploads to fetch; about 2 units per 50"
    )
    comments_per_video: int = Field(
        0,
        ge=0,
        le=100,
        description="Top comments to store per video, with their replies; 0 skips comments, "
        "otherwise about 1 unit per video",
    )


class FetchVideosResponse(BaseModel):
    channel_id: str
    videos_saved: int
    comments_saved: int = Field(0, description="Top-level comments and replies stored across the videos")
    quota_spent: int
    videos: list[VideoResponse] = Field(description="Newest first")


class FetchVideoResponse(BaseModel):
    quota_spent: int
    video: VideoResponse
