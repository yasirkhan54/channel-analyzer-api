from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from configurations.database_configuration import database
from configurations.environment_configuration import get_settings

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")
PKT_TZ = ZoneInfo("Asia/Karachi")
UTC_TZ = ZoneInfo("UTC")


def get_current_pacific_time() -> datetime:
    """Return the current datetime in the America/Los_Angeles timezone (R-2)."""
    return datetime.now(PACIFIC_TZ)


def get_current_pacific_date() -> date:
    """Return the current calendar date in America/Los_Angeles."""
    return get_current_pacific_time().date()


def get_next_reset_times(now_pacific: datetime | None = None) -> tuple[datetime, datetime, datetime]:
    """Calculate the next midnight reset in Pacific time, and return (pacific, pkt, utc)."""
    if now_pacific is None:
        now_pacific = get_current_pacific_time()
    next_day = now_pacific.date() + timedelta(days=1)
    reset_pacific = datetime.combine(next_day, time(0, 0, 0), tzinfo=PACIFIC_TZ)
    reset_pkt = reset_pacific.astimezone(PKT_TZ)
    reset_utc = reset_pacific.astimezone(UTC_TZ)
    return reset_pacific, reset_pkt, reset_utc


def _to_db_date(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)


async def get_quota_usage(quota_day: date | None = None, google_project_id: str = "default") -> int:
    """Retrieve total units spent for the specified Pacific date (defaults to today)."""
    target_date = quota_day or get_current_pacific_date()
    record = await database.quotausage.find_unique(
        where={
            "quotaDay_googleProjectId": {
                "quotaDay": _to_db_date(target_date),
                "googleProjectId": google_project_id,
            }
        }
    )
    return record.unitsSpent if record else 0


async def record_quota_spent(
    units: int, quota_day: date | None = None, google_project_id: str = "default"
) -> int:
    """Atomically increment the units spent for the Pacific day in the quota ledger (FR-9.1)."""
    if units <= 0:
        return await get_quota_usage(quota_day, google_project_id)

    target_date = quota_day or get_current_pacific_date()
    db_date = _to_db_date(target_date)

    record = await database.quotausage.upsert(
        where={
            "quotaDay_googleProjectId": {
                "quotaDay": db_date,
                "googleProjectId": google_project_id,
            }
        },
        data={
            "create": {
                "quotaDay": db_date,
                "googleProjectId": google_project_id,
                "unitsSpent": units,
            },
            "update": {
                "unitsSpent": {"increment": units},
            },
        },
    )
    return record.unitsSpent


async def check_quota_available(
    cost: int = 1, quota_day: date | None = None, google_project_id: str = "default"
) -> bool:
    """Check if the cost fits within the daily limit while preserving the safety margin (FR-9.3, R-16)."""
    settings = get_settings()
    daily_limit = settings.daily_quota_limit
    safety_margin = settings.quota_safety_margin

    spent = await get_quota_usage(quota_day, google_project_id)
    return (spent + cost) <= (daily_limit - safety_margin)


async def get_quota_status(
    quota_day: date | None = None, google_project_id: str = "default"
) -> dict[str, Any]:
    """Return the quota ledger status including units used, remaining, margin, and reset times (FR-9.2)."""
    settings = get_settings()
    daily_limit = settings.daily_quota_limit
    safety_margin = settings.quota_safety_margin

    spent = await get_quota_usage(quota_day, google_project_id)
    remaining = max(0, daily_limit - spent)
    reset_pacific, reset_pkt, reset_utc = get_next_reset_times()

    return {
        "units_used": spent,
        "units_remaining": remaining,
        "safety_margin": safety_margin,
        "daily_limit": daily_limit,
        "next_reset_pacific": reset_pacific.isoformat(),
        "next_reset_pkt": reset_pkt.isoformat(),
        "next_reset_utc": reset_utc.isoformat(),
        "used": spent,
        "remaining": remaining,
        "margin": safety_margin,
    }
