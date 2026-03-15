#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="gemini-live-agent"
REPO_NAME="gemini-live-agent-repo"
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest"

echo "PROJECT: $PROJECT_ID"

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project=$PROJECT_ID --quiet

# Create Artifact Registry repo
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID --quiet 2>/dev/null || echo "Repo already exists"

# Auth Docker
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

# Build and push image
gcloud builds submit ./gemini-live-agent \
  --tag $IMAGE \
  --project=$PROJECT_ID --quiet

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 3600 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION" \
  --project=$PROJECT_ID --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format "value(status.url)" \
  --project=$PROJECT_ID)

echo ""
echo "DEPLOYED: $SERVICE_URL"
echo "HEALTH: $SERVICE_URL/health"

# Quick health check
curl -s $SERVICE_URL/health
