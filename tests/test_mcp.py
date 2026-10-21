import asyncio

from fastapi.testclient import TestClient
from fastmcp import Client

from application import app, mcp_server
from services import health_service, quota_service

client = TestClient(app)


def _call(coroutine_fn):
    async def run():
        async with Client(mcp_server) as mcp_client:
            return await coroutine_fn(mcp_client)

    return asyncio.run(run())


def test_every_api_operation_is_a_tool_named_after_its_controller():
    tools = _call(lambda mcp_client: mcp_client.list_tools())
    names = {tool.name for tool in tools}
    operations = [op for ops in app.openapi()["paths"].values() for op in ops.values()]

    assert len(names) == len(operations)
    assert {"get_health", "get_quota", "resolve_channel", "create_fetch_job", "delete_channel"} <= names
    assert all("__" not in name and not name.endswith(("_get", "_post")) for name in names)


def test_tool_calls_the_api_with_the_client_key(monkeypatch):
    async def fake_quota_status() -> dict[str, object]:
        return {
            "units_used": 5,
            "units_remaining": 9995,
            "safety_margin": 200,
            "daily_limit": 10000,
            "next_reset_pacific": "2026-10-22T00:00:00-07:00",
            "next_reset_pkt": "2026-10-22T12:00:00+05:00",
            "next_reset_utc": "2026-10-22T07:00:00+00:00",
            "used": 5,
            "remaining": 9995,
            "margin": 200,
        }

    monkeypatch.setattr(quota_service, "get_quota_status", fake_quota_status)

    result = _call(lambda mcp_client: mcp_client.call_tool("get_quota", {}))

    assert result.structured_content["units_used"] == 5


def test_api_errors_come_back_as_tool_errors(monkeypatch):
    async def fake_check() -> bool:
        return False

    monkeypatch.setattr(health_service, "is_database_healthy", fake_check)

    result = _call(lambda mcp_client: mcp_client.call_tool("get_health", {}, raise_on_error=False))

    assert result.is_error
    assert "503" in result.content[0].text


def test_mcp_endpoint_needs_the_client_key():
    assert client.post("/mcp/", json={}).status_code == 401
