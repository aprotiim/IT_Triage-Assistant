from google.adk.agents import Agent

from it_triage_orchestrator.config import MODEL_NAME
from it_triage_orchestrator.mcp_client import build_mcp_toolset

access_agent = Agent(
    name="access_agent",
    model=MODEL_NAME,
    description=(
        "Handles account, VPN, and shared-drive/file access issues: "
        "checking current access and resetting VPN credentials."
    ),
    instruction=(
        "You resolve account, VPN, and drive-access problems for employees.\n\n"
        "Use check_user_access to verify whether a user currently has access "
        "to a named resource before claiming anything about their access. "
        "Valid resources are: shared_drive, vpn, finance_erp, "
        "engineering_repo.\n\n"
        "Use reset_vpn_credentials when a user reports they can't connect to "
        "VPN and needs new credentials.\n\n"
        "If a tool call fails (unknown user, unknown resource, or a "
        "deactivated account), explain the failure in plain language and "
        "suggest a concrete next step (e.g. 'ask IT to reactivate the "
        "account') instead of retrying blindly or inventing a result. "
        "Always state which user's email you looked up and what you found."
    ),
    tools=[build_mcp_toolset(tool_filter=["check_user_access", "reset_vpn_credentials"])],
)
