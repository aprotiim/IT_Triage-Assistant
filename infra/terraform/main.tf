locals {
  apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "iam.googleapis.com",
  ]
}

resource "google_project_service" "required" {
  for_each = toset(local.apis)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "images" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repo_id
  format        = "DOCKER"
  description   = "Container images for the IT triage orchestrator and MCP server."

  depends_on = [google_project_service.required]
}

# --- Service accounts ------------------------------------------------------
# Two identities, one per service, so IAM bindings below grant exactly the
# access each service needs and nothing more.

resource "google_service_account" "mcp_server" {
  project      = var.project_id
  account_id   = "it-triage-mcp-server"
  display_name = "IT Triage MCP server"

  depends_on = [google_project_service.required]
}

resource "google_service_account" "orchestrator" {
  project      = var.project_id
  account_id   = "it-triage-orchestrator"
  display_name = "IT Triage ADK orchestrator"

  depends_on = [google_project_service.required]
}

# The orchestrator calls Gemini via Vertex AI.
resource "google_project_iam_member" "orchestrator_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

# --- MCP server (Cloud Run) -------------------------------------------------

resource "google_cloud_run_v2_service" "mcp_server" {
  name                = "it-triage-mcp-server"
  project             = var.project_id
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.mcp_server.email

    containers {
      image = var.mcp_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }

  depends_on = [google_project_service.required]
}

# Deliberately no allUsers/allAuthenticatedUsers binding: only the
# orchestrator's own service account may invoke this service. This is the
# IAM-based service-to-service auth the assignment calls for, in place of a
# shared secret or an open endpoint — Cloud Run rejects any request that
# doesn't carry a valid ID token for an authorized invoker identity before
# it ever reaches the container.
resource "google_cloud_run_v2_service_iam_member" "orchestrator_can_invoke_mcp" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.mcp_server.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.orchestrator.email}"
}

# --- Orchestrator (Cloud Run) ------------------------------------------------

resource "google_cloud_run_v2_service" "orchestrator" {
  name                = "it-triage-orchestrator"
  project             = var.project_id
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.orchestrator.email

    containers {
      image = var.orchestrator_image

      ports {
        container_port = 8080
      }

      env {
        name  = "MCP_SERVER_URL"
        value = "${google_cloud_run_v2_service.mcp_server.uri}/mcp"
      }
      env {
        name  = "MCP_AUTH_MODE"
        value = "iam"
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "TRUE"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "ADK_MODEL"
        value = var.gemini_model
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }

  depends_on = [
    google_project_service.required,
    google_cloud_run_v2_service_iam_member.orchestrator_can_invoke_mcp,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "orchestrator_invokers" {
  for_each = toset(var.orchestrator_invoker_members)

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.orchestrator.name
  role     = "roles/run.invoker"
  member   = each.value
}
