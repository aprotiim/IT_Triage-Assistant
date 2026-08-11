import asyncio

from fastmcp import Client

from app import tools  # noqa: F401  (registers all @mcp.tool handlers)
from app.mcp_instance import mcp


def test_all_four_tools_are_registered_with_schemas():
    async def _list_tools():
        async with Client(mcp) as client:
            return await client.list_tools()

    registered = asyncio.run(_list_tools())
    names = {tool.name for tool in registered}
    assert names == {
        "check_user_access",
        "reset_vpn_credentials",
        "get_asset_status",
        "request_license_approval",
    }
    for tool in registered:
        schema = tool.inputSchema
        assert schema.get("type") == "object"
        assert schema.get("properties"), f"{tool.name} has no typed input schema"
