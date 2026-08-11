from fastmcp import FastMCP

mcp = FastMCP(
    name="it-support-tools",
    instructions=(
        "Tools for IT support triage: account/VPN access checks and resets, "
        "hardware asset status lookups, and software license approval "
        "requests. All tools are mocked against an in-memory dataset and "
        "raise a ToolError for their simulated failure mode."
    ),
)
