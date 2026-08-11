import os

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# InMemorySessionService is the ADK default when no session_service_uri is
# given, and it's what backs the "session persists across turns" requirement
# for a single running instance. See README "Known limitations" for why this
# is a deliberate scope cut rather than an oversight: a single Cloud Run
# instance with min-instances=1 keeps this true across requests, but it does
# not survive instance recycling. A production build would point this at
# VertexAiSessionService or a Cloud SQL-backed DatabaseSessionService.
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    allow_origins=["*"],
    web=True,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
