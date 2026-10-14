from pydantic import BaseModel, Field


class QuotaResponse(BaseModel):
    units_used: int = Field(..., description="Units spent today in the current Pacific day (R-2, FR-9.1)")
    units_remaining: int = Field(..., description="Units remaining today against daily limit")
    safety_margin: int = Field(..., description="Safety margin reserved for manual actions (FR-9.3)")
    daily_limit: int = Field(..., description="Total daily quota limit (default 10,000 units, R-1)")
    next_reset_pacific: str = Field(..., description="Next midnight quota reset timestamp in Pacific Time")
    next_reset_pkt: str = Field(..., description="Next quota reset timestamp in PKT (Asia/Karachi)")
    next_reset_utc: str = Field(..., description="Next quota reset timestamp in UTC")
    used: int = Field(..., description="Alias for units_used")
    remaining: int = Field(..., description="Alias for units_remaining")
    margin: int = Field(..., description="Alias for safety_margin")
