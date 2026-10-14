from datetime import datetime
from typing import Literal

from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from constants.application_constants import DEFAULT_TRANSCRIPT_LANGUAGES
from validators.common_validator import StoredRecordResponse


class FetchVideoTranscriptRequest(BaseModel):
    preferred_languages: list[str] = Field(
        default_factory=lambda: list(DEFAULT_TRANSCRIPT_LANGUAGES),
        description="Preferred language codes in order of priority",
    )


class FetchChannelTranscriptsRequest(BaseModel):
    preferred_languages: list[str] = Field(
        default_factory=lambda: list(DEFAULT_TRANSCRIPT_LANGUAGES),
        description="Preferred language codes in order of priority",
    )
    only_missing: bool = Field(
        default=True,
        description="Only fetch transcripts for videos not currently marked available",
    )


class TranscriptSegmentResponse(StoredRecordResponse):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=AliasGenerator(validation_alias=to_camel),
    )
    position: int
    start_seconds: float
    duration_seconds: float
    text: str


class TranscriptResponse(StoredRecordResponse):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=AliasGenerator(validation_alias=to_camel),
    )
    id: int
    video_id: str
    status: str
    language_code: str | None = None
    language_name: str | None = None
    is_generated: bool | None = None
    full_text: str | None = None
    segment_count: int = 0
    attempt_count: int = 0
    last_error: str | None = None
    fetched_at: datetime | None = None
    segments: list[TranscriptSegmentResponse] | None = None


class VideoTranscriptStatusItem(BaseModel):
    video_id: str
    title: str
    transcript_status: str
    language_code: str | None = None
    is_generated: bool | None = None
    attempt_count: int = 0
    last_error: str | None = None
    fetched_at: datetime | None = None


class ChannelTranscriptsFetchSummary(BaseModel):
    channel_id: str
    total_videos: int
    processed: int
    available: int
    none: int
    disabled: int
    failed: int
    blocked: int
    step_status: Literal["done", "partial", "blocked"]
