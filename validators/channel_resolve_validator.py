from pydantic import BaseModel, Field

from validators.channel_read_validator import ChannelResponse


class ChannelResolveRequest(BaseModel):
    input: str = Field(..., description="Channel URL, @handle, or channel ID (FR-1.1)")
    refresh: bool = Field(False, description="Force fresh fetch even if stored within 30 days (FR-1.4)")
    confirm_legacy: bool = Field(
        False, description="Confirm spending 100 quota units for legacy /c/ URLs via search (FR-1.5)"
    )


class ChannelResolveResponse(BaseModel):
    channel: ChannelResponse
    quota_spent: int = Field(..., description="Quota units spent on this resolution (FR-1.2)")
    cached: bool = Field(..., description="Whether data was returned from database without API call (FR-1.4)")
    resolved_id: str = Field(..., description="Resolved 24-character YouTube channel ID")
