variable "project_id" {
  description = "GCP project ID to deploy into."
  type        = string
}

variable "region" {
  description = "Cloud Run / Artifact Registry region."
  type        = string
  default     = "us-central1"
}

variable "artifact_repo_id" {
  description = "Artifact Registry Docker repository name."
  type        = string
  default     = "it-triage"
}

variable "mcp_image" {
  description = <<-EOT
    Fully-qualified image reference for the MCP server, built and pushed
    separately (see infra/deploy.sh or the CI workflow). Example:
    us-central1-docker.pkg.dev/PROJECT/it-triage/mcp-server:TAG
  EOT
  type = string
}

variable "orchestrator_image" {
  description = "Fully-qualified image reference for the orchestrator, built and pushed separately."
  type        = string
}

variable "gemini_model" {
  description = "Gemini model name used by the ADK agents (Gemini 2.x family, per assignment cost guidance)."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "orchestrator_invoker_members" {
  description = <<-EOT
    IAM members allowed to invoke the orchestrator's public endpoint, e.g.
    ["user:reviewer@example.com"]. Use ["allUsers"] to make the demo fully
    public for review (documented tradeoff in README). Leave empty and use
    `gcloud run services proxy` / ad-hoc IAM grants instead.
  EOT
  type    = list(string)
  default = []
}
