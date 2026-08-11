from it_triage_orchestrator import mcp_client


def test_build_mcp_toolset_passes_filter_url_and_headers(monkeypatch):
    captured = {}

    class FakeConnectionParams:
        def __init__(self, url, headers):
            captured["url"] = url
            captured["headers"] = headers

    class FakeToolset:
        def __init__(self, connection_params, tool_filter):
            captured["connection_params"] = connection_params
            captured["tool_filter"] = tool_filter

    monkeypatch.setattr(mcp_client, "StreamableHTTPConnectionParams", FakeConnectionParams)
    monkeypatch.setattr(mcp_client, "McpToolset", FakeToolset)
    monkeypatch.setattr(mcp_client.config, "MCP_SERVER_URL", "http://localhost:9999/mcp")
    monkeypatch.setattr(mcp_client.config, "MCP_AUTH_MODE", "none")

    mcp_client.build_mcp_toolset(["check_user_access"])

    assert captured["tool_filter"] == ["check_user_access"]
    assert captured["url"] == "http://localhost:9999/mcp"
    assert captured["headers"] == {}


def test_build_mcp_toolset_fetches_id_token_when_auth_mode_is_iam(monkeypatch):
    captured = {}

    class FakeConnectionParams:
        def __init__(self, url, headers):
            captured["headers"] = headers

    class FakeToolset:
        def __init__(self, connection_params, tool_filter):
            pass

    monkeypatch.setattr(mcp_client, "StreamableHTTPConnectionParams", FakeConnectionParams)
    monkeypatch.setattr(mcp_client, "McpToolset", FakeToolset)
    monkeypatch.setattr(mcp_client.config, "MCP_SERVER_URL", "https://mcp.example.run.app/mcp")
    monkeypatch.setattr(mcp_client.config, "MCP_AUTH_MODE", "iam")
    monkeypatch.setattr(mcp_client, "_fetch_id_token", lambda audience: "fake-id-token")

    mcp_client.build_mcp_toolset(["get_asset_status"])

    assert captured["headers"] == {"Authorization": "Bearer fake-id-token"}
