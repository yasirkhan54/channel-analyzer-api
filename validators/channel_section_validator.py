from datetime import datetime

from pydantic import BaseModel, Field

from validators.common_validator import StoredRecordResponse


class ChannelSectionResponse(StoredRecordResponse):
    id: str
    channel_id: str
    type: str = Field(
        description="What the shelf shows, lowercase as YouTube sends it, e.g. recentuploads, "
        "singleplaylist, multipleplaylists, multiplechannels; channelsectiontypeundefined for newer shelves"
    )
    title: str | None = Field(description="Set only for sections with a custom title")
    position: int = Field(description="Order on the channel page, from 0")
    playlist_ids: list[str] = Field(description="Playlists shown in the section")
    channel_ids: list[str] = Field(description="Channels featured in the section")
    fetched_at: datetime


class FetchChannelSectionsResponse(BaseModel):
    channel_id: str
    sections_saved: int
    quota_spent: int
    sections: list[ChannelSectionResponse]


class ChannelSectionListResponse(BaseModel):
    channel_id: str
    sections: list[ChannelSectionResponse]
