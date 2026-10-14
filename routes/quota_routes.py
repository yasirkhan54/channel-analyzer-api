from fastapi import APIRouter, Security
from fastapi.security import APIKeyHeader

from constants import route_descriptions
from constants.application_constants import CLIENT_KEY_HEADER
from controllers import quota_controller
from validators.quota_validator import QuotaResponse

client_key_header = APIKeyHeader(name=CLIENT_KEY_HEADER, auto_error=False)

router = APIRouter(tags=["Quota"])

router.add_api_route(
    "/quota",
    quota_controller.get_quota,
    methods=["GET"],
    response_model=QuotaResponse,
    dependencies=[Security(client_key_header)],
    summary="Today's quota usage, remaining units, safety margin and reset times",
    description=route_descriptions.QUOTA,
)
