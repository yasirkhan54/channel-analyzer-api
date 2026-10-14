from datetime import datetime
from typing import Literal, Self

from pydantic import Field, model_validator

from validators.common_validator import PageQuery, StoredRecordResponse

VideoSortField = Literal["published_at", "view_count", "like_count", "comment_count", "duration_seconds"]


class ChannelResponse(StoredRecordResponse):
    id: str
    title: str
    description: str | None
    custom_url: str | None
    country: str | None
    published_at: datetime | None
    subscriber_count: int | None = Field(description="Rounded by YouTube; empty when hidden (R-8)")
    subscriber_count_hidden: bool
    view_count: int | None
    video_count: int | None
    keywords: list[str]
    topic_categories: list[str]
    uploads_playlist_id: str | None
    tracked: bool
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime


class VideoResponse(StoredRecordResponse):
    id: str
    channel_id: str
    title: str
    description: str | None
    tags: list[str]
    published_at: datetime
    duration_iso: str | None
    duration_seconds: int | None
    is_short: bool = Field(description="Derived from duration; a heuristic, the API has no Shorts flag (R-9)")
    is_short_label: Literal["heuristic"] = "heuristic"
    upload_gap_seconds: int | None = Field(description="Seconds since the channel's previous upload (R-10)")
    view_count: int | None
    like_count: int | None
    comment_count: int | None
    category_id: str | None
    category_name: str | None
    default_language: str | None
    default_audio_language: str | None
    definition: str | None
    captions_available: bool | None
    made_for_kids: bool | None
    live_scheduled_start_at: datetime | None
    live_actual_start_at: datetime | None
    live_actual_end_at: datetime | None
    transcript_status: Literal["pending", "available", "none", "disabled", "blocked", "failed"]
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime


class VideoListQuery(PageQuery):
    sort_by: VideoSortField = "published_at"
    order: Literal["asc", "desc"] = "desc"
    is_short: bool | None = Field(None, description="true: Shorts only, false: long videos only (heuristic)")
    is_live: bool | None = Field(None, description="true: live streams only, false: normal uploads only")
    published_after: datetime | None = None
    published_before: datetime | None = None

    @model_validator(mode="after")
    def check_date_range(self) -> Self:
        if self.published_after and self.published_before and self.published_after > self.published_before:
            raise ValueError("published_after must not be later than published_before")
        return self
