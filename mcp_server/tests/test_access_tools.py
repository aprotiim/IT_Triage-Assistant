import pytest
from fastmcp.exceptions import ToolError

from app.tools.access import check_user_access, reset_vpn_credentials


def test_check_user_access_granted_for_provisioned_resource():
    result = check_user_access("alice@quantumintegrators.com", "vpn")
    assert result.has_access is True
    assert result.reason == "granted"


def test_check_user_access_not_provisioned_defaults_to_false():
    result = check_user_access("bob@quantumintegrators.com", "shared_drive")
    assert result.has_access is False
    assert result.reason == "not_provisioned"


def test_check_user_access_deactivated_account_has_no_access():
    result = check_user_access("old.contractor@quantumintegrators.com", "vpn")
    assert result.has_access is False
    assert result.reason == "account_deactivated"


def test_check_user_access_unknown_resource_raises_tool_error():
    with pytest.raises(ToolError, match="unknown_resource"):
        check_user_access("alice@quantumintegrators.com", "printer_room")


def test_check_user_access_unknown_user_raises_tool_error():
    with pytest.raises(ToolError, match="user_not_found"):
        check_user_access("nobody@quantumintegrators.com", "vpn")


def test_reset_vpn_credentials_success():
    result = reset_vpn_credentials("bob@quantumintegrators.com")
    assert result.status == "success"
    assert result.credentials_expire_at


def test_reset_vpn_credentials_deactivated_account_raises_tool_error():
    with pytest.raises(ToolError, match="account_deactivated"):
        reset_vpn_credentials("old.contractor@quantumintegrators.com")
