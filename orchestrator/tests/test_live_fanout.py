"""End-to-end tests against the real Gemini model on Vertex AI.

These are the tests that actually exercise the checklist items "multi-agent
fan-out" and "session state persists across turns" for real, rather than by
inspecting agent wiring. They need live Vertex AI credentials, so they're
skipped by default (and in CI) and only run when explicitly opted into:

    gcloud auth application-default login
    export GOOGLE_CLOUD_PROJECT=<your-project>
    export RUN_LIVE_ADK_TESTS=1
    pytest tests/test_live_fanout.py -v
"""

import os

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types

from it_triage_orchestrator.agent import root_agent

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_ADK_TESTS"),
    reason=(
        "Requires live Vertex AI credentials. Set RUN_LIVE_ADK_TESTS=1 and "
        "authenticate with `gcloud auth application-default login` to run."
    ),
)


async def _run_and_collect(runner: InMemoryRunner, session_id: str, user_id: str, text: str):
    message = types.Content(role="user", parts=[types.Part(text=text)])
    tool_calls = []
    final_text = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message
    ):
        for call in event.get_function_calls():
            tool_calls.append(call.name)
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or final_text
    return tool_calls, final_text


async def test_multi_domain_request_fans_out_to_two_specialists_and_merges():
    runner = InMemoryRunner(agent=root_agent, app_name="it-triage-test")
    session = await runner.session_service.create_session(
        app_name="it-triage-test", user_id="tester-fanout"
    )

    tool_calls, final_text = await _run_and_collect(
        runner,
        session.id,
        "tester-fanout",
        "My VPN keeps disconnecting for alice@quantumintegrators.com, and "
        "separately I need Figma license-approved for the same user.",
    )

    assert "access_agent" in tool_calls
    assert "licensing_agent" in tool_calls
    assert final_text


async def test_session_state_persists_across_two_turns():
    runner = InMemoryRunner(agent=root_agent, app_name="it-triage-test")
    session = await runner.session_service.create_session(
        app_name="it-triage-test", user_id="tester-session"
    )

    await _run_and_collect(
        runner,
        session.id,
        "tester-session",
        "Can bob@quantumintegrators.com access the shared drive?",
    )
    _, final_text = await _run_and_collect(
        runner, session.id, "tester-session", "Now reset his VPN credentials too."
    )

    assert "bob" in final_text.lower()
