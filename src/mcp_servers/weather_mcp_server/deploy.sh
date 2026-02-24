#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Weather MCP Server - Cloud Run Deployment${NC}"
echo "=========================================="
echo ""

# Load environment variables from .env
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables from .env...${NC}"
    export $(sed -e '/^ *#/d' -e '/^$/d' -e 's/ *= */=/' -e "s/'//g" -e 's/"//g' .env | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Check required environment variables
REQUIRED_VARS=("SERVICE_NAME" "LOCATION" "PROJECT_ID" "GOOGLE_CLIENT_ID" "GOOGLE_CLIENT_SECRET")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please update your .env file with the required values."
    exit 1
fi

# Validate OAuth credentials are not placeholder values
if [[ "$GOOGLE_CLIENT_ID" == "your-client-id"* ]] || [[ "$GOOGLE_CLIENT_SECRET" == "your-client-secret"* ]]; then
    echo -e "${RED}Error: OAuth credentials not configured${NC}"
    echo "Please update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
    echo ""
    echo "To get credentials:"
    echo "1. Go to https://console.cloud.google.com/apis/credentials"
    echo "2. Create OAuth 2.0 Client ID"
    echo "3. Add redirect URI: https://\${SERVICE_NAME}-\${PROJECT_NUMBER}.${LOCATION}.run.app/oauth/callback"
    exit 1
fi

echo -e "${GREEN}Configuration:${NC}"
echo "  Service Name: $SERVICE_NAME"
echo "  Location: $LOCATION"
echo "  Project ID: $PROJECT_ID"
echo "  Client ID: ${GOOGLE_CLIENT_ID:0:20}..."
echo ""

# Confirm deployment
read -p "Deploy to Cloud Run? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Setting gcloud project...${NC}"
gcloud config set project "$PROJECT_ID"

echo ""
echo -e "${GREEN}Step 2: Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo ""
echo -e "${GREEN}Step 3: Building and deploying to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$LOCATION" \
  --project "$PROJECT_ID" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}" \
  --set-env-vars "GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}" \
  --set-env-vars "OAUTH_SCOPES=${OAUTH_SCOPES:-openid email profile}" \
  --set-env-vars "MCP_SCOPE=${MCP_SCOPE:-user}"

echo ""
echo -e "${GREEN}Step 4: Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$LOCATION" \
  --format="value(status.url)")

echo "Service URL: $SERVICE_URL"

# Update MCP_SERVER_URL
export MCP_SERVER_URL="${SERVICE_URL}/mcp"

# Update the deployment with the correct MCP_SERVER_URL
echo ""
echo -e "${GREEN}Step 5: Updating MCP_SERVER_URL...${NC}"
gcloud run services update "$SERVICE_NAME" \
  --region "$LOCATION" \
  --set-env-vars "MCP_SERVER_URL=${MCP_SERVER_URL}"

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "=========================================="
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. Update OAuth Redirect URI in Google Cloud Console:"
echo "   ${YELLOW}${SERVICE_URL}/oauth/callback${NC}"
echo ""
echo "2. Access your server:"
echo "   - Home: ${SERVICE_URL}"
echo "   - OAuth Login: ${SERVICE_URL}/oauth/login"
echo "   - MCP Endpoint: ${SERVICE_URL}/mcp"
echo ""
echo "3. Test the deployment:"
echo "   ${YELLOW}curl ${SERVICE_URL}${NC}"
echo ""
echo "=========================================="

# Optional: Add IAM policy binding if PROJECT_NUMBER is set
if [ -n "$PROJECT_NUMBER" ]; then
    echo ""
    read -p "Add IAM policy binding for compute service account? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Adding IAM policy binding...${NC}"
        gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
            --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
            --role="roles/run.invoker" \
            --region="$LOCATION"
        echo -e "${GREEN}✅ IAM policy binding added${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"
