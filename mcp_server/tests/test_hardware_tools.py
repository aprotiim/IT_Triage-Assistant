import pytest
from fastmcp.exceptions import ToolError

from app.tools.hardware import get_asset_status


def test_get_asset_status_active_device():
    result = get_asset_status("LAP-1001")
    assert result.status == "active"
    assert result.owner_email == "alice@quantumintegrators.com"
    assert result.notes == ""


def test_get_asset_status_in_repair_includes_note():
    result = get_asset_status("LAP-1002")
    assert result.status == "in_repair"
    assert "repair" in result.notes.lower()


def test_get_asset_status_unknown_tag_raises_tool_error():
    with pytest.raises(ToolError, match="asset_not_found"):
        get_asset_status("LAP-9999")
