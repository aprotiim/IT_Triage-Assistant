from google.adk.agents import Agent
from google.adk.tools import AgentTool

from it_triage_orchestrator.config import MODEL_NAME
from it_triage_orchestrator.sub_agents.access_agent import access_agent
from it_triage_orchestrator.sub_agents.hardware_agent import hardware_agent
from it_triage_orchestrator.sub_agents.licensing_agent import licensing_agent

# Specialists are wrapped as AgentTool, not attached via sub_agents=. ADK's
# sub_agents/transfer_to_agent pattern hands the whole turn's control to one
# sub-agent at a time and doesn't return to the parent for synthesis, which
# doesn't fit "call two specialists and merge their results into one
# response." AgentTool lets the root call any number of specialists inside
# a single turn, in either order, and then compose the final answer itself.
root_agent = Agent(
    name="it_triage_orchestrator",
    model=MODEL_NAME,
    description=(
        "Front door for IT support requests: classifies intent, routes to "
        "the right specialist(s), and synthesizes one coherent response."
    ),
    instruction=(
        "You are the front door for IT support. Read the user's request and "
        "decide which specialist(s) to call:\n"
        "- access_agent: account, VPN, or shared-drive/file access problems.\n"
        "- hardware_agent: laptop/device status, repair, or asset questions.\n"
        "- licensing_agent: requests to get software licensed or approved.\n\n"
        "A single request can span more than one domain (for example, 'my "
        "VPN is broken AND I need Adobe licensed'). When that happens, call "
        "every specialist the request actually needs — in any order — "
        "before you respond. Don't call a specialist the request doesn't "
        "need just to be thorough.\n\n"
        "Never guess at a specialist's results yourself; only report what "
        "the specialist agent actually returned. Once you have every "
        "result, merge them into a single response organized by topic, "
        "with concrete next steps and any request/ticket IDs included. If a "
        "specialist reports a failure, surface it plainly instead of hiding "
        "it or claiming success."
    ),
    tools=[
        AgentTool(agent=access_agent),
        AgentTool(agent=hardware_agent),
        AgentTool(agent=licensing_agent),
    ],
)
