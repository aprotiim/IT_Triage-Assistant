import uuid

from fastmcp.exceptions import ToolError

from app.data import DIRECTORY, SOFTWARE_CATALOG
from app.mcp_instance import mcp
from app.schemas import LicenseApprovalResult


def request_license_approval(
    user_email: str, software_name: str, justification: str = ""
) -> LicenseApprovalResult:
    """Submit a software license request for approval.

    Auto-approves low-cost software for active employees; routes higher-cost
    software to manager review when a justification is provided, otherwise
    denies it outright.
    """
    if user_email not in DIRECTORY:
        raise ToolError(f"user_not_found: no directory record for '{user_email}'")

    catalog_key = software_name.strip().lower().replace(" ", "_")
    catalog_entry = SOFTWARE_CATALOG.get(catalog_key)
    if catalog_entry is None:
        raise ToolError(
            f"software_not_catalogued: '{software_name}' is not in the "
            f"license catalog. Known software: {sorted(SOFTWARE_CATALOG)}"
        )

    request_id = f"LIC-{uuid.uuid4().hex[:8].upper()}"
    user = DIRECTORY[user_email]

    if not user["active"]:
        return LicenseApprovalResult(
            request_id=request_id,
            user_email=user_email,
            software_name=software_name,
            status="denied",
            reason="Requesting account is not an active employee.",
        )

    if catalog_entry["auto_approve"]:
        return LicenseApprovalResult(
            request_id=request_id,
            user_email=user_email,
            software_name=software_name,
            status="approved",
            reason="Auto-approved: low-cost tier software for an active employee.",
        )

    if not justification.strip():
        return LicenseApprovalResult(
            request_id=request_id,
            user_email=user_email,
            software_name=software_name,
            status="denied",
            reason="No business justification provided for a paid-tier license.",
        )

    return LicenseApprovalResult(
        request_id=request_id,
        user_email=user_email,
        software_name=software_name,
        status="pending_manager_review",
        reason=f"Routed to {user['manager_email']} for cost-tier approval.",
    )


mcp.tool(request_license_approval)
