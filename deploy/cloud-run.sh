#!/usr/bin/env bash
# Manual deployment script for Google Cloud Run.
# Usage: ./deploy/cloud-run.sh
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated: gcloud auth login
#   2. Required env vars set (copy from .env.example and fill in values)
#   3. Artifact Registry repository already created (see step 2 below)

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="google-ads-mcp"
REPO="google-ads-mcp"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/server"

# ── Step 1: Enable required APIs ───────────────────────────────────────────
echo "→ Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --project="${PROJECT_ID}"

# ── Step 2: Create Artifact Registry repository (idempotent) ───────────────
echo "→ Creating Artifact Registry repository..."
gcloud artifacts repositories create "${REPO}" \
  --repository-format=docker \
  --location="${REGION}" \
  --project="${PROJECT_ID}" 2>/dev/null || true

# ── Step 3: Store secrets in Secret Manager ────────────────────────────────
echo "→ Storing secrets in Secret Manager..."
store_secret() {
  local name="$1"
  local value="$2"
  # Create secret if it doesn't exist, then add a new version
  gcloud secrets describe "${name}" --project="${PROJECT_ID}" &>/dev/null \
    || gcloud secrets create "${name}" --project="${PROJECT_ID}" --replication-policy=automatic
  echo -n "${value}" | gcloud secrets versions add "${name}" --data-file=- --project="${PROJECT_ID}"
}

store_secret "GOOGLE_ADS_DEVELOPER_TOKEN"          "${GOOGLE_ADS_DEVELOPER_TOKEN:?}"
store_secret "GOOGLE_ADS_CLIENT_ID"                "${GOOGLE_ADS_CLIENT_ID:?}"
store_secret "GOOGLE_ADS_CLIENT_SECRET"            "${GOOGLE_ADS_CLIENT_SECRET:?}"
store_secret "GOOGLE_ADS_REFRESH_TOKEN"            "${GOOGLE_ADS_REFRESH_TOKEN:?}"
store_secret "GOOGLE_ADS_LOGIN_CUSTOMER_ID"        "${GOOGLE_ADS_LOGIN_CUSTOMER_ID:-}"
store_secret "FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID"     "${FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID:?}"
store_secret "FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET" "${FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET:?}"

# ── Step 4: Build and push Docker image ────────────────────────────────────
echo "→ Configuring Docker authentication..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "→ Building Docker image..."
docker build -t "${IMAGE}:latest" .

echo "→ Pushing Docker image..."
docker push "${IMAGE}:latest"

# ── Step 5: Deploy to Cloud Run ────────────────────────────────────────────
echo "→ Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}:latest" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --set-secrets="\
GOOGLE_ADS_DEVELOPER_TOKEN=GOOGLE_ADS_DEVELOPER_TOKEN:latest,\
GOOGLE_ADS_CLIENT_ID=GOOGLE_ADS_CLIENT_ID:latest,\
GOOGLE_ADS_CLIENT_SECRET=GOOGLE_ADS_CLIENT_SECRET:latest,\
GOOGLE_ADS_REFRESH_TOKEN=GOOGLE_ADS_REFRESH_TOKEN:latest,\
GOOGLE_ADS_LOGIN_CUSTOMER_ID=GOOGLE_ADS_LOGIN_CUSTOMER_ID:latest,\
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID:latest,\
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET:latest"

# ── Step 6: Print service URL and Claude setup instructions ────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format='value(status.url)')

echo ""
echo "✓ Deployed successfully!"
echo ""
echo "Service URL: ${SERVICE_URL}"
echo "MCP endpoint: ${SERVICE_URL}/mcp"
echo ""
echo "Next: Update FASTMCP_SERVER_BASE_URL to ${SERVICE_URL}"
echo "Then re-run this script or update the Cloud Run service env var."
echo ""
echo "Claude.ai / Claude mobile setup:"
echo "  Settings → Integrations → Add MCP server"
echo "  URL: ${SERVICE_URL}/mcp"
