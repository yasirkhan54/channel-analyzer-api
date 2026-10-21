import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastmcp.utilities.lifespan import combine_lifespans

from configurations.database_configuration import database
from configurations.environment_configuration import get_settings
from constants.application_constants import (
    API_OPERATION_ORDER,
    API_TAGS,
    ASSETS_URL,
    CLIENT_KEY_HEADER,
    MCP_URL,
    OPENAPI_URL,
    SERVICE_DESCRIPTION,
    SERVICE_TITLE,
    SERVICE_VERSION,
)
from middleware.client_key_middleware import ClientKeyMiddleware
from middleware.rate_limit_middleware import RateLimitMiddleware
from routes import (
    caption_routes,
    category_routes,
    channel_management_routes,
    channel_read_routes,
    channel_resolve_routes,
    channel_section_routes,
    comment_read_routes,
    docs_routes,
    fetch_job_routes,
    health_routes,
    playlist_read_routes,
    quota_routes,
    refresh_routes,
    search_routes,
    transcript_routes,
    video_fetch_routes,
)
from services import fetch_job_runner
from utilities.mcp_server import create_mcp_server
from utilities.openapi_examples import add_examples


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await database.connect()
    runner_task = asyncio.create_task(fetch_job_runner.run_schedule())
    try:
        yield
    finally:
        runner_task.cancel()
        if database.is_connected():
            await database.disconnect()


get_settings()  # fail fast on missing or invalid env

app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    lifespan=lifespan,
    docs_url=None,  # served by routes/docs_routes.py with the service theme
    openapi_url=OPENAPI_URL,
    redoc_url=None,
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ClientKeyMiddleware)


def _ordered_paths(paths: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    """Order paths and their methods by API_OPERATION_ORDER; anything not listed goes last."""
    rank = {operation: index for index, operation in enumerate(API_OPERATION_ORDER)}

    def position(path: str, method: str) -> int:
        return rank.get(f"{method.upper()} {path}", len(rank))

    ordered = {
        path: dict(sorted(operations.items(), key=lambda item: position(path, item[0])))
        for path, operations in paths.items()
    }
    return dict(sorted(ordered.items(), key=lambda item: min(position(item[0], m) for m in item[1])))


def custom_openapi() -> dict[str, object]:
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=SERVICE_TITLE,
        version=SERVICE_VERSION,
        description=SERVICE_DESCRIPTION,
        routes=app.routes,
    )
    # Keep the "APIKeyHeader" scheme that the routers' Security(client_key_header) generates;
    # replacing it left the operations pointing at a scheme Swagger UI could not find.
    schemes = openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schemes.setdefault("APIKeyHeader", {"type": "apiKey", "in": "header", "name": CLIENT_KEY_HEADER})
    schemes["APIKeyHeader"]["description"] = "Enter your static client API key"
    openapi_schema["tags"] = API_TAGS
    openapi_schema["paths"] = _ordered_paths(openapi_schema["paths"])
    add_examples(openapi_schema)
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.include_router(health_routes.router)
app.include_router(docs_routes.router)
app.mount(ASSETS_URL, StaticFiles(directory=Path(__file__).parent / "public" / "assets"), name="assets")
app.include_router(channel_read_routes.router)
app.include_router(video_fetch_routes.router)
app.include_router(channel_resolve_routes.router)
app.include_router(comment_read_routes.router)
app.include_router(playlist_read_routes.router)
app.include_router(quota_routes.router)
app.include_router(search_routes.router)
app.include_router(refresh_routes.router)
app.include_router(transcript_routes.router)
app.include_router(channel_section_routes.router)
app.include_router(caption_routes.router)
app.include_router(category_routes.router)
app.include_router(channel_management_routes.router)
app.include_router(fetch_job_routes.router)

# MCP server for AI agents, built from the routes above (so it goes last). It needs the client key too.
mcp_server = create_mcp_server(app)
# Mounted at MCP_URL, so the endpoint inside the MCP app is its root.
mcp_app = mcp_server.http_app(path="/")
app.mount(MCP_URL, mcp_app)
app.router.lifespan_context = combine_lifespans(lifespan, mcp_app.lifespan)
