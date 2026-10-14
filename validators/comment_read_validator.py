from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from validators.common_validator import PageQuery, StoredRecordResponse


class CommentResponse(StoredRecordResponse):
    id: str
    video_id: str
    parent_id: str | None
    text: str
    author_display_name: str | None
    author_channel_id: str | None
    like_count: int
    total_reply_count: int | None
    published_at: datetime
    edited_at: datetime | None
    fetched_at: datetime


class CommentThreadResponse(CommentResponse):
    replies: list[CommentResponse]


class CommentListQuery(PageQuery):
    sort_by: Literal["like_count", "published_at"] = "like_count"
    order: Literal["asc", "desc"] = "desc"


class FetchCommentsRequest(BaseModel):
    max_comments: int = Field(100, ge=1, le=1000, description="Top-level comments to fetch; 100 per unit")
    include_replies: bool = Field(
        True,
        description="Also store every reply (replies beyond the first few cost 1 unit per 100 per thread)",
    )
    order: Literal["relevance", "time"] = Field("relevance", description="relevance (top) or time (newest)")


class FetchCommentsResponse(BaseModel):
    video_id: str
    comments_saved: int = Field(description="Top-level comments stored")
    replies_saved: int
    comments_disabled: bool
    quota_spent: int
