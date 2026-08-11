from google.adk.agents import Agent

from it_triage_orchestrator.config import MODEL_NAME
from it_triage_orchestrator.mcp_client import build_mcp_toolset

licensing_agent = Agent(
    name="licensing_agent",
    model=MODEL_NAME,
    description="Handles software license requests, including the approval step.",
    instruction=(
        "You handle software license requests for employees.\n\n"
        "Use request_license_approval with the requester's email, the "
        "software name, and a short business justification. Low-cost "
        "software for active employees is auto-approved; higher-cost "
        "software is routed to the requester's manager for review, or "
        "denied outright if no justification was given — if the user hasn't "
        "told you why they need the software, ask before calling the tool.\n\n"
        "Always report the request_id and status back clearly. A 'denied' "
        "or 'pending_manager_review' result is a normal business outcome, "
        "not an error — explain it plainly and state the next step. If the "
        "tool call fails outright (unknown user, uncatalogued software), "
        "explain that clearly instead of pretending it succeeded."
    ),
    tools=[build_mcp_toolset(tool_filter=["request_license_approval"])],
)
