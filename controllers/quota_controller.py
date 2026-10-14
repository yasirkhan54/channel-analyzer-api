from services import quota_service
from validators.quota_validator import QuotaResponse


async def get_quota() -> QuotaResponse:
    status = await quota_service.get_quota_status()
    return QuotaResponse(**status)
