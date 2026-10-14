from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader

from constants import route_descriptions
from constants.application_constants import CLIENT_KEY_HEADER, HOME_URL
from controllers import health_controller
from validators.health_validator import HealthResponse

# Declared so the docs show the client key; the client key middleware enforces it.
client_key_header = APIKeyHeader(name=CLIENT_KEY_HEADER, auto_error=False)

router = APIRouter(tags=["Health"])

router.add_api_route(
    "/health",
    health_controller.get_health,
    methods=["GET"],
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse}},
    summary="Service and database health",
    description=route_descriptions.HEALTH,
)
router.add_api_route(
    HOME_URL,
    health_controller.get_home_page,
    methods=["GET"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
