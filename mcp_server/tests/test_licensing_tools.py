import pytest
from fastmcp.exceptions import ToolError

from app.tools.licensing import request_license_approval


def test_low_cost_software_is_auto_approved():
    result = request_license_approval("alice@quantumintegrators.com", "Figma", "design work")
    assert result.status == "approved"
    assert result.request_id.startswith("LIC-")


def test_high_cost_software_with_justification_goes_to_manager_review():
    result = request_license_approval(
        "bob@quantumintegrators.com", "Adobe Creative Cloud", "client deliverables"
    )
    assert result.status == "pending_manager_review"
    assert "priya@quantumintegrators.com" in result.reason


def test_high_cost_software_without_justification_is_denied():
    result = request_license_approval("bob@quantumintegrators.com", "Adobe Creative Cloud", "")
    assert result.status == "denied"


def test_deactivated_user_is_denied():
    result = request_license_approval(
        "old.contractor@quantumintegrators.com", "Figma", "still need it"
    )
    assert result.status == "denied"


def test_uncatalogued_software_raises_tool_error():
    with pytest.raises(ToolError, match="software_not_catalogued"):
        request_license_approval("alice@quantumintegrators.com", "Random Obscure App", "reasons")


def test_unknown_user_raises_tool_error():
    with pytest.raises(ToolError, match="user_not_found"):
        request_license_approval("nobody@quantumintegrators.com", "Figma", "reasons")
