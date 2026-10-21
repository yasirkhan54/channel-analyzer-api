"""Stdio bridge for AI agents: `python -m utilities.mcp_connect`.

Proxies stdio to the running API's MCP endpoint and adds the client key from .env, so the key
is never written into an agent's MCP config. Set ANALYZER_MCP_URL to reach another address.
"""

import os

from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.server import create_proxy

from configurations.environment_configuration import get_settings
from constants.application_constants import CLIENT_KEY_HEADER, MCP_URL, SERVICE_NAME

DEFAULT_MCP_ENDPOINT = f"http://localhost:8010{MCP_URL}/"


def main() -> None:
    transport = StreamableHttpTransport(
        os.environ.get("ANALYZER_MCP_URL", DEFAULT_MCP_ENDPOINT),
        headers={CLIENT_KEY_HEADER: get_settings().client_api_key.get_secret_value()},
    )
    create_proxy(transport, name=SERVICE_NAME).run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
