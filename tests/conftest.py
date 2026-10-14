import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ["CLIENT_API_KEY"] = "test-client-key"

import pytest  # noqa: E402

from middleware.rate_limit_middleware import reset_rate_limits  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Every test starts with an empty rate limit window, so the suite size never trips the limit."""
    reset_rate_limits()
    yield
