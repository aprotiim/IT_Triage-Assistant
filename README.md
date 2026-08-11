# IT Support Triage Assistant

A multi-agent orchestration system built for the take-home assignment in
[`Multi-Agent-Orchestration-Assignment.docx`](Multi-Agent-Orchestration-Assignment.docx):
a Root Orchestrator (Google ADK) classifies a plain-language IT support
request, routes it to one or more specialist agents, each specialist calls
tools on a standalone MCP server, and the orchestrator synthesizes one
response.

See [`docs/architecture.md`](docs/architecture.md) for the diagram and the
reasoning behind each architectural decision (why `AgentTool` instead of
`sub_agents`, why three agents and not more, why each specialist gets a
filtered `McpToolset`, how tool failures are handled).

## Repo layout

```
mcp_server/                  Standalone MCP server (FastMCP, Streamable HTTP)
  app/
    mcp_instance.py           Shared FastMCP() instance
    schemas.py                Pydantic output schemas for all 4 tools
    data.py                   Mock in-memory directory/assets/catalog
    tools/                    access.py, hardware.py, licensing.py
    server.py                 Entrypoint (`python -m app.server`)
  tests/                      Tool logic + registration tests (no network)
  Dockerfile

orchestrator/                 ADK agents + FastAPI entrypoint
  main.py                     Cloud Run entrypoint (ADK's get_fast_api_app)
  it_triage_orchestrator/
    agent.py                  root_agent (AgentTool fan-out over 3 specialists)
    mcp_client.py              McpToolset builder + Cloud Run IAM auth (ID tokens)
    config.py                  Env-driven config (model name, MCP URL, auth mode)
    sub_agents/                access_agent.py, hardware_agent.py, licensing_agent.py
  tests/
    test_routing.py             Deterministic agent-wiring tests (no LLM/network)
    test_mcp_client.py          Unit tests for the McpToolset/IAM wiring
    test_live_fanout.py         Real end-to-end fan-out + session-persistence
                                 tests against live Gemini (opt-in, see below)
  Dockerfile

infra/
  terraform/                   Cloud Run x2, IAM bindings, Artifact Registry
  deploy.sh                    gcloud-only alternative to Terraform

.github/workflows/ci.yml       Lint (ruff) + test both services on push
docs/architecture.md           Diagram + design rationale
```

## Functional requirements checklist

| Requirement | Where |
|---|---|
| Routes ≥3 distinct request types | `it_triage_orchestrator/agent.py` instruction; access/hardware/licensing each independently reachable |
| Multi-agent fan-out test | `orchestrator/tests/test_live_fanout.py::test_multi_domain_request_fans_out_to_two_specialists_and_merges` |
| Each sub-agent calls ≥1 MCP tool | `sub_agents/*.py` — each wired to its own filtered `McpToolset` |
| Graceful tool-failure handling | Every tool raises `ToolError` for its failure mode; agent instructions require surfacing it, not hiding it (see `mcp_server/tests/test_*_tools.py` for the failure-mode tests) |
| Session persists across ≥2 turns | `orchestrator/tests/test_live_fanout.py::test_session_state_persists_across_two_turns` |
| Structured logs/traces | ADK's built-in per-agent/per-tool event trace via `get_fast_api_app` (`/apps/.../sessions/.../` event history); see "Observability" below |
| Deployed and reachable on Cloud Run | `infra/terraform/` or `infra/deploy.sh` — see "Deploy to GCP" |

## Local development

Requires Python 3.12+.

**1. Run the MCP server:**

```bash
cd mcp_server
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt   # Windows: .venv\Scripts\pip
.venv/bin/python -m app.server        # serves Streamable HTTP on :8080/mcp
```

**2. Run the orchestrator against it**, with IAM auth disabled for local dev
(no Cloud Run in front of the MCP server locally, so there's no ID token to
fetch):

```bash
cd orchestrator
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt

gcloud auth application-default login   # so ADK can call Vertex AI Gemini
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=<your-project>
export GOOGLE_CLOUD_LOCATION=us-central1
export MCP_SERVER_URL=http://localhost:8080/mcp
export MCP_AUTH_MODE=none

.venv/bin/adk web .                     # interactive dev UI at localhost:8000
# or: .venv/bin/python main.py          # the same FastAPI app Cloud Run runs
```

## Testing strategy

Tests are deliberately split into two tiers:

- **Deterministic, credential-free** (`test_routing.py`, `test_mcp_client.py`,
  everything in `mcp_server/tests/`): pure Python, no network, no GCP
  credentials. These run in CI on every push and assert the things that
  don't require a live model call — tool logic and failure modes, agent
  wiring (which specialists are attached, which MCP tools each is scoped
  to), and the IAM header-injection logic.
- **Live, credential-gated** (`orchestrator/tests/test_live_fanout.py`):
  runs the real root agent through an ADK `Runner` against live Gemini, and
  asserts the actual model calls both `access_agent` and `licensing_agent`
  for a cross-domain request, and that a follow-up turn reuses session
  context. This is the test that proves fan-out isn't faked — but it needs
  real Vertex AI credentials and costs real (small) tokens, so it's
  `skipif`'d unless `RUN_LIVE_ADK_TESTS=1` is set, and CI doesn't run it.
  This was a deliberate scope call given the ASAP timeline: a green CI badge
  should mean "the code is correct," not "and also we spent API credits on
  every commit." Run it locally with:

  ```bash
  gcloud auth application-default login
  export GOOGLE_CLOUD_PROJECT=<your-project>
  export RUN_LIVE_ADK_TESTS=1
  cd orchestrator && pytest tests/test_live_fanout.py -v
  ```

Run everything else with `pytest -q` from `mcp_server/` or `orchestrator/`.

## Observability

ADK's FastAPI server exposes each turn's full event trace (which agent ran,
which `AgentTool`/MCP tool calls it made, in order, with arguments and
results) via the session endpoints
(`GET /apps/{app}/users/{user}/sessions/{session}`). That satisfies
"structured logs/traces showing which agent handled which part of a request
and which tools were called" without hand-rolled logging. For the Loom
walkthrough, the plan is to show this endpoint alongside the chat response
for the fan-out example.

## Deploy to GCP

Both services are built from their own `Dockerfile` (not
`adk deploy cloud_run`'s auto-containerization) so the orchestrator's IAM
auth logic and both services' dependency pins are fully explicit and
reproducible.

**Option A — Terraform** (`infra/terraform/`):

```bash
cd infra/terraform
terraform init
terraform apply \
  -var="project_id=<your-project>" \
  -var="mcp_image=us-central1-docker.pkg.dev/<your-project>/it-triage/mcp-server:latest" \
  -var="orchestrator_image=us-central1-docker.pkg.dev/<your-project>/it-triage/orchestrator:latest"
```

Terraform provisions the Artifact Registry repo, both service accounts, both
Cloud Run services, and the IAM bindings — but expects the two images to
already exist (build/push them with Cloud Build first, or run
`infra/deploy.sh` once, which does both).

**Option B — `infra/deploy.sh`** (gcloud only, no Terraform):

```bash
PROJECT_ID=<your-project> ./infra/deploy.sh
```

Builds both images with Cloud Build, deploys the MCP server with
`--no-allow-unauthenticated`, grants the orchestrator's service account
`roles/run.invoker` on it, and deploys the orchestrator. Set
`ORCHESTRATOR_PUBLIC=true` to make the orchestrator itself publicly
reachable (see the tradeoff note it prints, and in "Known limitations"
below).

## Known limitations and what I'd do with more time

- **Session persistence is in-memory.** `InMemorySessionService` (ADK's
  default) satisfies the "2-turn follow-up" requirement for a single
  running instance, but doesn't survive Cloud Run scaling to zero or
  instance recycling. With more time: `DatabaseSessionService` against
  Cloud SQL, or `VertexAiSessionService`.
- **Orchestrator-facing auth is a documented judgment call, not fully
  resolved.** The MCP server is unambiguously IAM-locked (service-to-service).
  Whether the *orchestrator's* public endpoint should itself require IAM
  (most secure, but blocks a casual reviewer) or allow unauthenticated
  access (easiest to demo) is genuinely ambiguous for a take-home meant to
  be reviewed quickly — `infra/deploy.sh` defaults to private and offers
  `ORCHESTRATOR_PUBLIC=true` as an explicit opt-in for the review window.
- **ID token for the MCP call is fetched once per `McpToolset`
  construction**, not refreshed. Fine for a container's lifetime in this
  assignment's scope; a longer-lived deployment would wrap it in a
  refreshing credential.
- **No rate limiting / retry policy** on MCP tool calls beyond what ADK does
  by default. Given more time I'd add bounded retries with backoff for
  transient (non-`ToolError`) failures specifically, while still failing
  fast on the simulated business failures.
- **No persistent ticketing backend.** All state is in-memory mock data in
  `mcp_server/app/data.py`, reset on every container restart — appropriate
  for a mocked assignment, not for a real IT system.

## Deliverables

- Repository: *(this repo)*
- Deployed Cloud Run URL: *(fill in after running `infra/deploy.sh` or
  Terraform against a real GCP project — see "Deploy to GCP" above)*
- Loom walkthrough: *(link — single-domain + multi-domain fan-out demo)*
- Architecture diagram: [`docs/architecture.md`](docs/architecture.md)
  (Mermaid, renders directly on GitHub — a pragmatic substitute for a
  separate draw.io/Excalidraw export given the timeline; happy to export a
  static image too if preferred)
