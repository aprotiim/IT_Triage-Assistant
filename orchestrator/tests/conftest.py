import os

# Set before any `it_triage_orchestrator` import so agent/toolset construction
# never needs real GCP credentials for the deterministic unit test suite.
# Constructing an ADK Agent with a model *string* and an MCPToolset with
# connection params does not itself call out to Vertex AI or the MCP
# server — those calls only happen once a Runner actually invokes the agent,
# which only the credential-gated live tests in test_live_fanout.py do.
os.environ.setdefault("MCP_SERVER_URL", "http://localhost:8080/mcp")
os.environ.setdefault("MCP_AUTH_MODE", "none")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
