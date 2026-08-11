from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

from it_triage_orchestrator import config


def _fetch_id_token(audience: str) -> str:
    # Imported lazily so environments that only run the credential-free unit
    # tests (MCP_AUTH_MODE=none) never need google-auth's ADC machinery.
    import google.auth.transport.requests
    import google.oauth2.id_token

    request = google.auth.transport.requests.Request()
    return google.oauth2.id_token.fetch_id_token(request, audience)


def _mcp_headers() -> dict[str, str]:
    if config.MCP_AUTH_MODE == "none":
        return {}
    token = _fetch_id_token(config.MCP_SERVER_URL)
    return {"Authorization": f"Bearer {token}"}


def build_mcp_toolset(tool_filter: list[str]) -> McpToolset:
    """Build an McpToolset scoped to a specialist agent's own tools only.

    Every specialist gets its own toolset (rather than one shared toolset)
    so each agent's tool_filter documents, in code, exactly which of the
    shared MCP server's tools that domain is allowed to call.
    """
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=config.MCP_SERVER_URL,
            headers=_mcp_headers(),
        ),
        tool_filter=tool_filter,
    )
