import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from configurations.environment_configuration import get_settings
from constants.application_constants import CLIENT_KEY_HEADER, is_public_path

# Per-client in-memory timestamp store
_request_records: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    """Clear in-memory rate limit records (primarily for testing)."""
    _request_records.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces a per-client-key rate limit across a sliding window (FR-12.3)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if is_public_path(request.url.path):
            return await call_next(request)

        settings = get_settings()
        max_requests = settings.rate_limit_requests
        window_seconds = settings.rate_limit_window_seconds

        client_key = request.headers.get(CLIENT_KEY_HEADER, "anonymous")
        now = time.monotonic()
        history = _request_records[client_key]

        # Evict timestamps outside the sliding window
        threshold = now - window_seconds
        while history and history[0] < threshold:
            history.popleft()

        if len(history) >= max_requests:
            retry_after = max(1, int(history[0] + window_seconds - now) + 1)
            return JSONResponse(
                {"detail": "Rate limit exceeded. Too many requests."},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        history.append(now)
        return await call_next(request)
