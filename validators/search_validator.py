from datetime import datetime
from typing import Literal, Self

from prisma.enums import CommentMode
from pydantic import BaseModel, Field, model_validator

from validators.common_validator import StoredRecordResponse
from validators.fetch_job_validator import FetchJobResponse

SEARCH_UNIT_COST = 100  # search.list costs 100 units per page (R-3)
MAX_SEARCH_PAGES = 5
MAX_RESULTS_PER_PAGE = 50

SearchOrder = Literal["relevance", "date", "rating", "title", "viewCount", "videoCount"]


class SearchRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=200)
    type: Literal["video", "channel"] = "video"
    region_code: str | None = Field(None, pattern=r"^[A-Za-z]{2}$", description="ISO 3166-1 alpha-2")
    relevance_language: str | None = Field(None, min_length=2, max_length=10, description="e.g. en, ur")
    published_after: datetime | None = None
    published_before: datetime | None = None
    order: SearchOrder = "relevance"
    pages: int = Field(1, ge=1, le=MAX_SEARCH_PAGES, description="Each page costs 100 quota units")
    results_per_page: int = Field(MAX_RESULTS_PER_PAGE, ge=1, le=MAX_RESULTS_PER_PAGE)

    @model_validator(mode="after")
    def check_date_range(self) -> Self:
        if self.published_after and self.published_before and self.published_after > self.published_before:
            raise ValueError("published_after must not be later than published_before")
        return self

    @property
    def quota_cost(self) -> int:
        return self.pages * SEARCH_UNIT_COST


class SearchEstimateResponse(BaseModel):
    quota_cost: int
    units_available: int = Field(description="Units left today above the safety margin")
    allowed: bool


class SearchResultResponse(StoredRecordResponse):
    rank: int
    result_type: Literal["video", "channel"]
    video_id: str | None
    channel_id: str | None = Field(description="The channel found, or the channel of the video found")
    title: str | None


class SearchQueryResponse(StoredRecordResponse):
    id: int
    keyword: str
    type: Literal["video", "channel"]
    filters: dict | None
    quota_spent: int
    fetched_at: datetime
    created_at: datetime


class SearchQueryDetailResponse(SearchQueryResponse):
    results: list[SearchResultResponse]


class QueueSearchResultRequest(BaseModel):
    """Options for the full fetch that a search result starts (FR-7.4)."""

    comment_mode: CommentMode = CommentMode.top_100
    transcripts_requested: bool | None = None


class QueueSearchResultResponse(BaseModel):
    job: FetchJobResponse
