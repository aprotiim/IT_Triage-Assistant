from fastmcp.exceptions import ToolError

from app.data import DIRECTORY, KNOWN_RESOURCES, RESOURCE_ACCESS, days_from_now_iso, now_iso
from app.mcp_instance import mcp
from app.schemas import AccessCheckResult, VpnResetResult


def check_user_access(user_email: str, resource: str) -> AccessCheckResult:
    """Check whether a user currently has access to a named internal resource.

    Valid resources: shared_drive, vpn, finance_erp, engineering_repo.
    """
    if resource not in KNOWN_RESOURCES:
        raise ToolError(
            f"unknown_resource: '{resource}' is not a recognized resource. "
            f"Known resources: {sorted(KNOWN_RESOURCES)}"
        )
    if user_email not in DIRECTORY:
        raise ToolError(f"user_not_found: no directory record for '{user_email}'")

    user = DIRECTORY[user_email]
    if not user["active"]:
        return AccessCheckResult(
            user_email=user_email,
            resource=resource,
            has_access=False,
            reason="account_deactivated",
            checked_at=now_iso(),
        )

    has_access = RESOURCE_ACCESS.get((user_email, resource), False)
    return AccessCheckResult(
        user_email=user_email,
        resource=resource,
        has_access=has_access,
        reason="granted" if has_access else "not_provisioned",
        checked_at=now_iso(),
    )


def reset_vpn_credentials(user_email: str) -> VpnResetResult:
    """Issue fresh VPN credentials for a user, invalidating the old ones."""
    if user_email not in DIRECTORY:
        raise ToolError(f"user_not_found: no directory record for '{user_email}'")
    if not DIRECTORY[user_email]["active"]:
        raise ToolError(
            f"account_deactivated: '{user_email}' is not an active account "
            "and cannot receive VPN credentials"
        )

    return VpnResetResult(
        user_email=user_email,
        status="success",
        credentials_expire_at=days_from_now_iso(90),
        message=f"New VPN credentials issued for {user_email}.",
    )


mcp.tool(check_user_access)
mcp.tool(reset_vpn_credentials)
