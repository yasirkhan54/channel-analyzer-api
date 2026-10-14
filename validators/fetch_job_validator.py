from datetime import datetime
from typing import Any

from prisma.enums import (
    CommentMode,
    FetchJobStage,
    FetchJobStatus,
    FetchJobType,
    TranscriptStepStatus,
)
from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from validators.common_validator import StoredRecordResponse


class CreateFetchJobRequest(BaseModel):
    channel_input: str = Field(
        description="Channel URL, @handle, or channel ID (FR-1.1)",
    )
    comment_mode: CommentMode = Field(
        default=CommentMode.top_100,
        description="Comment fetching mode (R-23: top_100, all, skip)",
    )
    type: FetchJobType = Field(
        default=FetchJobType.full_fetch,
        description="Job type (full_fetch, stats_refresh, full_refresh)",
    )
    transcripts_requested: bool | None = Field(
        default=None,
        description="Whether to fetch transcripts; defaults to True if < 200 videos, False otherwise (R-24)",
    )


class FetchJobResponse(StoredRecordResponse):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=AliasGenerator(validation_alias=to_camel),
    )
    id: int
    channel_input: str
    channel_id: str | None = None
    type: FetchJobType
    comment_mode: CommentMode
    status: FetchJobStatus
    stage: FetchJobStage | None = None
    transcripts_requested: bool
    transcript_step_status: TranscriptStepStatus
    videos_found: int
    videos_done: int
    comments_fetched: int
    playlists_done: int
    transcripts_done: int
    transcripts_missing: int
    transcripts_blocked: int
    resume_cursor: dict[str, Any] | None = None
    quota_spent: int
    error_detail: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class EstimateFetchJobRequest(BaseModel):
    channel_input: str
    comment_mode: CommentMode = CommentMode.top_100
    transcripts_requested: bool | None = None


class FetchJobEstimateResponse(BaseModel):
    channel_id: str | None = None
    channel_title: str | None = None
    video_count: int
    comment_mode: CommentMode
    estimated_quota_units_min: int
    estimated_quota_units_max: int
    transcripts_requested: bool
    estimated_transcript_time_seconds: int
    estimated_transcript_time_formatted: str
    quota_available: bool
    current_quota_remaining: int
    warning: str | None = None
