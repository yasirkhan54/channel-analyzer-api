from pathlib import Path

from fastapi.responses import HTMLResponse, JSONResponse

from services import health_service
from validators.health_validator import HealthResponse

HOME_PAGE = Path(__file__).resolve().parent.parent / "public" / "home.html"


async def get_health() -> JSONResponse:
    healthy = await health_service.is_database_healthy()
    body = HealthResponse(status="ok" if healthy else "error", database="ok" if healthy else "error")
    return JSONResponse(body.model_dump(), status_code=200 if healthy else 503)


async def get_home_page() -> HTMLResponse:
    return HTMLResponse(HOME_PAGE.read_text(encoding="utf-8"))
