output "cloud_run_service_url" {
  value       = google_cloud_run_v2_service.agent_service.uri
  description = "The public HTTPS URL of the deployed Gemini Live Agent Cloud Run service."
}

output "artifact_registry_instructions" {
  value       = "Repository '${google_artifact_registry_repository.gemini_repo.name}' created. Run 'docker push ${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:latest' before running 'terraform apply'."
  description = "Docker push instructions for the Artifact Registry pipeline."
}

output "service_account_email" {
  value       = google_service_account.cloudrun_sa.email
  description = "The IAM Service Account successfully bound to Vertex AI User role."
}
