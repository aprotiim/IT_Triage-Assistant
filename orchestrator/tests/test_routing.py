from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from it_triage_orchestrator.agent import root_agent
from it_triage_orchestrator.sub_agents.access_agent import access_agent
from it_triage_orchestrator.sub_agents.hardware_agent import hardware_agent
from it_triage_orchestrator.sub_agents.licensing_agent import licensing_agent


def test_root_agent_routes_to_all_three_specialists():
    wrapped_names = {t.agent.name for t in root_agent.tools if isinstance(t, AgentTool)}
    assert wrapped_names == {"access_agent", "hardware_agent", "licensing_agent"}


def test_root_agent_uses_agent_tool_composition_not_transfer():
    # AgentTool (not sub_agents=/transfer_to_agent) is what lets the root
    # call more than one specialist within a single turn and then synthesize
    # their results itself — required for multi-domain fan-out requests.
    assert root_agent.sub_agents == []
    assert len(root_agent.tools) == 3
    assert all(isinstance(t, AgentTool) for t in root_agent.tools)


def test_each_specialist_has_exactly_one_scoped_mcp_toolset():
    for agent in (access_agent, hardware_agent, licensing_agent):
        assert len(agent.tools) == 1
        assert isinstance(agent.tools[0], McpToolset)


def test_root_agent_instruction_names_every_specialist_by_tool_name():
    for name in ("access_agent", "hardware_agent", "licensing_agent"):
        assert name in root_agent.instruction


def test_specialist_agents_have_distinct_single_sentence_descriptions():
    descriptions = {
        access_agent.description,
        hardware_agent.description,
        licensing_agent.description,
    }
    assert len(descriptions) == 3
    assert all(descriptions)
