terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Values for variables usually come from terraform.tfvars or CLI
variable "project_id" {
  type        = string
  description = "The GCP project ID"
  default     = "gen-lang-client-0158119347"
}

variable "region" {
  type        = string
  description = "The GCP region to deploy to"
  default     = "us-central1"
}

variable "service_name" {
  type        = string
  description = "The name of the Cloud Run service"
  default     = "gemini-live-agent"
}

# 1. Enable Required Cloud APIs
resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "aiplatform_api" {
  service = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry_api" {
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# 2. Create Artifact Registry Repository
resource "google_artifact_registry_repository" "gemini_repo" {
  provider      = google
  location      = var.region
  repository_id = var.service_name
  description   = "Docker repository for Gemini Live Agent"
  format        = "DOCKER"

  depends_on = [google_project_service.artifactregistry_api]
}

# 3. Create a Custom Service Account for Cloud Run
resource "google_service_account" "cloudrun_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Cloud Run Service Account for Gemini Live Agent"
}

# 4. Bind Vertex AI User Role to our Service Account (For Gemini Live Grounding)
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# 5. Cloud Run Service Deployment
resource "google_cloud_run_v2_service" "agent_service" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloudrun_sa.email
    
    containers {
      # Important: Initialize Terraform with a valid image inside AR
      # Before terraform apply, you must build & push your Docker image here.
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:latest"
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "FALSE"
      }
      
      env {
        name  = "GOOGLE_API_KEY"
        value = "AIzaSyBfkkYMRFpDcUYTl2sivsGPCofcy6SlUKA"
      }
      
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      ports {
        container_port = 8080
      }
    }
    
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    
    timeout = "3600s" # 1 hour for long-lived WebSocket connections
  }

  depends_on = [
    google_project_service.run_api,
    google_artifact_registry_repository.gemini_repo,
    google_project_iam_member.vertex_ai_user
  ]
}

# 6. Allow unauthenticated ingress to the Cloud Run service (Public Web Access)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.agent_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
