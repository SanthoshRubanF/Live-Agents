$env:Path += ";$env:LOCALAPPDATA\Google\google-cloud-sdk\bin"
$PROJECT_ID = "gen-lang-client-0158119347"
$REGION = "us-central1"
$SERVICE_NAME = "gemini-live-agent"
$REPO_NAME = "gemini-live-agent-repo"
$IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME`:latest"

Write-Host "PROJECT: $PROJECT_ID"
gcloud services enable run.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project=$PROJECT_ID --quiet
gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION --project=$PROJECT_ID --quiet 2>$null
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
gcloud builds submit . --tag $IMAGE --project=$PROJECT_ID --quiet
gcloud run deploy $SERVICE_NAME --image $IMAGE --platform managed --region $REGION --allow-unauthenticated --memory 1Gi --cpu 1 --timeout 3600 --min-instances 0 --max-instances 10 --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=FALSE,GOOGLE_API_KEY=AIzaSyAdGmjF-GB4uxrYOdWfFR9B_vy4dK-ASjA,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION" --project=$PROJECT_ID --quiet

$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)" --project=$PROJECT_ID
Write-Host ""
Write-Host "DEPLOYED: $SERVICE_URL"
Write-Host "HEALTH: $SERVICE_URL/health"

curl.exe -s "$SERVICE_URL/health"
