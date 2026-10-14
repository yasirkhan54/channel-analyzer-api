from pydantic import BaseModel, Field


class ChannelTrackingRequest(BaseModel):
    tracked: bool = Field(description="Marks a channel you follow; nothing refreshes it automatically yet")
