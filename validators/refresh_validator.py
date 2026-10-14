from prisma.enums import CommentMode
from pydantic import BaseModel, Field

from validators.channel_read_validator import ChannelResponse
from validators.fetch_job_validator import FetchJobResponse


class StatsRefreshResponse(BaseModel):
    channel: ChannelResponse
    videos_refreshed: int = Field(description="Stored videos whose current counts were refreshed")
    quota_spent: int = Field(description="YouTube Data API units spent by this refresh")


class FullRefreshRequest(BaseModel):
    comment_mode: CommentMode = CommentMode.top_100
    transcripts_requested: bool | None = None


class FullRefreshResponse(BaseModel):
    job: FetchJobResponse
