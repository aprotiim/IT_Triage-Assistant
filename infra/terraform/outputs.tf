output "mcp_server_url" {
  description = "Internal URL of the MCP server Cloud Run service (IAM-protected, not directly browsable)."
  value       = google_cloud_run_v2_service.mcp_server.uri
}

output "orchestrator_url" {
  description = "URL of the orchestrator Cloud Run service."
  value       = google_cloud_run_v2_service.orchestrator.uri
}

output "orchestrator_service_account" {
  value = google_service_account.orchestrator.email
}

output "mcp_server_service_account" {
  value = google_service_account.mcp_server.email
}
