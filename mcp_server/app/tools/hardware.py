from fastmcp.exceptions import ToolError

from app.data import ASSETS, now_iso
from app.mcp_instance import mcp
from app.schemas import AssetStatus


def get_asset_status(asset_tag: str) -> AssetStatus:
    """Look up the current status of a hardware asset by its asset tag (e.g. 'LAP-1001')."""
    asset = ASSETS.get(asset_tag)
    if asset is None:
        raise ToolError(f"asset_not_found: no asset with tag '{asset_tag}'")

    notes = ""
    if asset["status"] == "in_repair":
        notes = "Device is currently checked in with IT hardware repair."
    elif asset["status"] == "retired":
        notes = "Device has been decommissioned and is no longer supported."

    return AssetStatus(
        asset_tag=asset_tag,
        owner_email=asset["owner_email"],
        status=asset["status"],
        last_seen=now_iso(),
        battery_health_pct=asset["battery_health_pct"],
        notes=notes,
    )


mcp.tool(get_asset_status)
