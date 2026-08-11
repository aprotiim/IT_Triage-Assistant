import os

# Gemini 2.x family on Vertex AI, per the assignment's cost guidance. The ADK
# LlmAgent resolves this lazily against Vertex AI at generate-time, so
# constructing an Agent with this string does not itself require credentials
# (that's what keeps the routing/wiring unit tests credential-free).
MODEL_NAME = os.environ.get("ADK_MODEL", "gemini-2.5-flash")

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8080/mcp")

# "iam" fetches a Google-signed ID token (via ADC) and sends it as a Bearer
# token, matching a Cloud Run service deployed with --no-allow-unauthenticated.
# "none" is for local dev against an MCP server with no IAM in front of it.
MCP_AUTH_MODE = os.environ.get("MCP_AUTH_MODE", "iam")
