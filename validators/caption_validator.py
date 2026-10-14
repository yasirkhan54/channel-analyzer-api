from datetime import datetime

from pydantic import BaseModel, Field

from validators.common_validator import StoredRecordResponse


class CaptionTrackResponse(StoredRecordResponse):
    id: str
    video_id: str
    language: str = Field(description="BCP-47 language code, e.g. en, ur")
    name: str | None = Field(description="Track name shown in the player; empty for most tracks")
    track_kind: str = Field(description="standard (uploaded by the owner), asr (auto-generated) or forced")
    audio_track_type: str | None
    is_cc: bool | None = Field(description="Closed captions for the deaf and hard of hearing")
    is_large: bool | None
    is_easy_reader: bool | None
    is_draft: bool | None
    is_auto_synced: bool | None
    status: str | None = Field(description="serving, syncing or failed")
    failure_reason: str | None
    last_updated: datetime | None
    fetched_at: datetime


class FetchCaptionsResponse(BaseModel):
    video_id: str
    tracks_saved: int
    quota_spent: int
    tracks: list[CaptionTrackResponse]


class CaptionTrackListResponse(BaseModel):
    video_id: str
    tracks: list[CaptionTrackResponse]
