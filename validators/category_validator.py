from datetime import datetime

from pydantic import BaseModel, Field

from validators.common_validator import StoredRecordResponse


class FetchCategoriesRequest(BaseModel):
    region_code: str = Field("US", pattern=r"^[A-Za-z]{2}$", description="ISO 3166-1 alpha-2, e.g. US, PK")
    language: str = Field(
        "en", min_length=2, max_length=10, description="Language of the titles, e.g. en, ur"
    )


class VideoCategoryResponse(StoredRecordResponse):
    id: str
    title: str
    assignable: bool = Field(description="Whether uploaders can pick this category for a video")
    channel_id: str | None
    region_code: str
    language: str
    fetched_at: datetime


class FetchCategoriesResponse(BaseModel):
    categories_saved: int
    quota_spent: int
    categories: list[VideoCategoryResponse]
