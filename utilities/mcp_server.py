import re
from typing import Any

from fastapi import FastAPI
from fastmcp import FastMCP

from configurations.environment_configuration import get_settings
from constants.application_constants import CLIENT_KEY_HEADER, MCP_INSTRUCTIONS, SERVICE_NAME


def _tool_names(openapi_schema: dict[str, Any]) -> dict[str, str]:
    """Map each operationId to its controller function name.

    FastAPI builds operationIds as name + path + method with non-word characters as "_"
    (get_channel_channels__channel_id__get), so dropping that suffix leaves the name.
    """
    names = {}
    for path, operations in openapi_schema["paths"].items():
        for method, operation in operations.items():
            suffix = re.sub(r"\W", "_", path) + f"_{method}"
            operation_id = operation["operationId"]
            names[operation_id] = operation_id.removesuffix(suffix)
    return names


def create_mcp_server(app: FastAPI) -> FastMCP:
    """Build the MCP server from the app's routes: every API operation becomes a tool.

    Tools call the API in-process with the client key, so the key check, rate limit and
    validation stay the same as over HTTP. Tool names are the controller function names.
    """
    return FastMCP.from_fastapi(
        app,
        name=SERVICE_NAME,
        instructions=MCP_INSTRUCTIONS,
        mcp_names=_tool_names(app.openapi()),
        httpx_client_kwargs={
            "headers": {CLIENT_KEY_HEADER: get_settings().client_api_key.get_secret_value()},
            # Fetches from YouTube can take a while; reads return at once.
            "timeout": 300,
        },
    )
