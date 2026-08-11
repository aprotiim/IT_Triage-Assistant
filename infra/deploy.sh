#!/usr/bin/env bash
# Reproduces the Cloud Run deployment without Terraform, using gcloud only.
# Run from the repo root in a POSIX shell (Cloud Shell, WSL, Git Bash, macOS/Linux).
#
# Required env vars:
#   PROJECT_ID   - target GCP project
# Optional env vars:
#   REGION                (default: us-central1)
#   ARTIFACT_REPO          (default: it-triage)
#   GEMINI_MODEL            (default: gemini-2.5-flash)
#   ORCHESTRATOR_PUBLIC     (default: "" ; set to "true" to allow public,
#                            unauthenticated access to the orchestrator for
#                            a review demo — see README "Known limitations")
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID to your GCP project id}"
REGION="${REGION:-us-central1}"
ARTIFACT_REPO="${ARTIFACT_REPO:-it-triage}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
ORCHESTRATOR_PUBLIC="${ORCHESTRATOR_PUBLIC:-}"

MCP_SA="it-triage-mcp-server"
ORCH_SA="it-triage-orchestrator"
MCP_SERVICE="it-triage-mcp-server"
ORCH_SERVICE="it-triage-orchestrator"
REPO_HOST="${REGION}-docker.pkg.dev"
MCP_IMAGE="${REPO_HOST}/${PROJECT_ID}/${ARTIFACT_REPO}/mcp-server:latest"
ORCH_IMAGE="${REPO_HOST}/${PROJECT_ID}/${ARTIFACT_REPO}/orchestrator:latest"

echo "== Enabling required APIs =="
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  iam.googleapis.com \
  cloudbuild.googleapis.com \
  --project "${PROJECT_ID}"

echo "== Artifact Registry repo =="
gcloud artifacts repositories describe "${ARTIFACT_REPO}" \
  --project "${PROJECT_ID}" --location "${REGION}" >/dev/null 2>&1 || \
gcloud artifacts repositories create "${ARTIFACT_REPO}" \
  --project "${PROJECT_ID}" --location "${REGION}" --repository-format=docker \
  --description "Container images for the IT triage orchestrator and MCP server"

gcloud auth configure-docker "${REPO_HOST}" --quiet

echo "== Service accounts =="
gcloud iam service-accounts describe "${MCP_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project "${PROJECT_ID}" >/dev/null 2>&1 || \
gcloud iam service-accounts create "${MCP_SA}" \
  --project "${PROJECT_ID}" --display-name "IT Triage MCP server"

gcloud iam service-accounts describe "${ORCH_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project "${PROJECT_ID}" >/dev/null 2>&1 || \
gcloud iam service-accounts create "${ORCH_SA}" \
  --project "${PROJECT_ID}" --display-name "IT Triage ADK orchestrator"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:${ORCH_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/aiplatform.user" --condition=None >/dev/null

echo "== Building and pushing images (Cloud Build, no local Docker needed) =="
gcloud builds submit ./mcp_server --project "${PROJECT_ID}" --tag "${MCP_IMAGE}"
gcloud builds submit ./orchestrator --project "${PROJECT_ID}" --tag "${ORCH_IMAGE}"

echo "== Deploying MCP server (private: no --allow-unauthenticated) =="
gcloud run deploy "${MCP_SERVICE}" \
  --project "${PROJECT_ID}" --region "${REGION}" \
  --image "${MCP_IMAGE}" \
  --service-account "${MCP_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --no-allow-unauthenticated \
  --port 8080

MCP_URL="$(gcloud run services describe "${MCP_SERVICE}" \
  --project "${PROJECT_ID}" --region "${REGION}" --format='value(status.url)')"

echo "== Granting the orchestrator's identity run.invoker on the MCP server =="
gcloud run services add-iam-policy-binding "${MCP_SERVICE}" \
  --project "${PROJECT_ID}" --region "${REGION}" \
  --member "serviceAccount:${ORCH_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/run.invoker"

echo "== Deploying orchestrator =="
ORCH_UNAUTH_FLAG="--no-allow-unauthenticated"
if [ "${ORCHESTRATOR_PUBLIC}" = "true" ]; then
  ORCH_UNAUTH_FLAG="--allow-unauthenticated"
fi

gcloud run deploy "${ORCH_SERVICE}" \
  --project "${PROJECT_ID}" --region "${REGION}" \
  --image "${ORCH_IMAGE}" \
  --service-account "${ORCH_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
  ${ORCH_UNAUTH_FLAG} \
  --port 8080 \
  --set-env-vars "MCP_SERVER_URL=${MCP_URL}/mcp,MCP_AUTH_MODE=iam,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},ADK_MODEL=${GEMINI_MODEL}"

ORCH_URL="$(gcloud run services describe "${ORCH_SERVICE}" \
  --project "${PROJECT_ID}" --region "${REGION}" --format='value(status.url)')"

echo
echo "== Done =="
echo "MCP server (private):  ${MCP_URL}"
echo "Orchestrator:           ${ORCH_URL}"
if [ "${ORCHESTRATOR_PUBLIC}" != "true" ]; then
  echo
  echo "Orchestrator requires an authenticated caller. Grant yourself access with:"
  echo "  gcloud run services add-iam-policy-binding ${ORCH_SERVICE} \\"
  echo "    --project ${PROJECT_ID} --region ${REGION} \\"
  echo "    --member user:you@example.com --role roles/run.invoker"
  echo "Then call it with an identity token, e.g.:"
  echo "  curl -H \"Authorization: Bearer \$(gcloud auth print-identity-token)\" ${ORCH_URL}/list-apps"
fi
