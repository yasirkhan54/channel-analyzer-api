import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from configurations.environment_configuration import get_settings
from constants.application_constants import CLIENT_KEY_HEADER, is_public_path


class ClientKeyMiddleware(BaseHTTPMiddleware):
    """Requires the static client key header on every path except the public paths (R-15)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if is_public_path(request.url.path):
            return await call_next(request)

        expected = get_settings().client_api_key.get_secret_value()
        provided = request.headers.get(CLIENT_KEY_HEADER, "")
        if not secrets.compare_digest(provided.encode(), expected.encode()):
            return JSONResponse({"detail": "Invalid or missing client key"}, status_code=401)

        return await call_next(request)
