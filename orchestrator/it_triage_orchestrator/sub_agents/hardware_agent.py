from google.adk.agents import Agent

from it_triage_orchestrator.config import MODEL_NAME
from it_triage_orchestrator.mcp_client import build_mcp_toolset

hardware_agent = Agent(
    name="hardware_agent",
    model=MODEL_NAME,
    description="Handles device and hardware issues: asset status, repair state, ownership.",
    instruction=(
        "You resolve laptop/device hardware questions for employees.\n\n"
        "Use get_asset_status with an asset tag (e.g. 'LAP-1001') to look up "
        "a device's current status, owner, and health. If the user doesn't "
        "give you an asset tag, ask for it rather than guessing one.\n\n"
        "If the asset tag isn't found, say so plainly and suggest the user "
        "confirm the tag on the device's asset sticker or with IT inventory "
        "instead of retrying with a made-up tag."
    ),
    tools=[build_mcp_toolset(tool_filter=["get_asset_status"])],
)
