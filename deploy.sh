#!/bin/bash
set -e

echo "=========================================="
echo "  Food & Health Tracking App Deployment   "
echo "=========================================="
echo ""

# Prompt for Project ID
read -p "Enter your Google Cloud Project ID: " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Project ID cannot be empty. Exiting."
    exit 1
fi

echo ""
echo "Setting active project to: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

echo "Deploying to Cloud Run..."
gcloud run deploy food-health-app \
    --source . \
    --allow-unauthenticated \
    --region us-central1 \
    --project "$PROJECT_ID"

echo ""
echo "=========================================="
echo "           Deployment Complete!           "
echo "=========================================="
