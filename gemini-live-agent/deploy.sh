#!/bin/bash
set -e

echo "=================================================="
echo " Deploying Gemini Live Agent to Google Cloud Run"
echo "=================================================="

# 1. Set PROJECT_ID from gcloud config
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: No Google Cloud project configured."
    echo "Run 'gcloud config set project YOUR_PROJECT_ID' first."
    exit 1
fi
echo "Using project: $PROJECT_ID"

# 2. Enable APIs
echo "Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    aiplatform.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

# 3. Create Artifact Registry repo if not exists
REPO_NAME="gemini-live-agent"
REGION="us-central1"
echo "Checking Artifact Registry repository '$REPO_NAME' in $REGION..."
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION > /dev/null 2>&1; then
    echo "Creating repository $REPO_NAME..."
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for Gemini Live Agent"
else
    echo "Repository $REPO_NAME already exists."
fi

# 4. Run gcloud builds submit
echo "Submitting to Cloud Build..."
gcloud builds submit --config cloudbuild.yaml .

# 5. Print the Cloud Run service URL when done
echo "Fetching Cloud Run service URL..."
SERVICE_URL=$(gcloud run services describe gemini-live-agent \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo "=================================================="
echo "✅ Deployment Complete!"
echo "Service URL: $SERVICE_URL"

# 6. Print the health check URL
HEALTH_URL="${SERVICE_URL}/health"
echo "Health Check URL: $HEALTH_URL"

# 7. Run a quick curl health check on the deployed URL
echo "Testing health endpoint..."
curl -s $HEALTH_URL | jq || echo "Could not fetch or parse JSON from $HEALTH_URL"
echo ""
echo "=================================================="
