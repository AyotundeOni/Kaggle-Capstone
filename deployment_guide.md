# Patho-Bot Cloud Run Deployment Guide (with Firestore)

This guide details how to deploy the Patho-Bot application to **Google Cloud Run** with a persistent **Firestore Database**.

## 1. Prerequisites
1.  **Google Cloud Project**: Create one at [console.cloud.google.com](https://console.cloud.google.com).
2.  **gcloud CLI**: Installed and authenticated (`gcloud auth login`).
3.  **APIs Enabled**:
    *   Cloud Run API
    *   Artifact Registry API
    *   Firestore API
    *   Vertex AI API (for Gemini)

## 2. Set Up Firestore (Database)
Before deploying, you must create the database in your Google Cloud Project.

1.  Go to the **[Firestore Console](https://console.cloud.google.com/firestore)**.
2.  Click **Create Database**.
3.  Select **Native Mode** (Recommended for mobile/web apps).
4.  **Location**: Choose a region (e.g., `us-central1` or `europe-west1`).
    *   *Tip: Choose the same region where you plan to deploy Cloud Run for lowest latency.*
5.  Click **Create**.

*That's it! The app is configured to automatically create the `patients` collection when data is saved.*

## 3. Deployment Steps

### Step A: Build & Push Image
Run these commands in your terminal:

```bash
# 1. Set your Project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# 2. Build the image using Cloud Build
# This packages your app, dependencies, and model into a container
gcloud builds submit --tag gcr.io/$PROJECT_ID/patho-bot
```

### Step B: Deploy to Cloud Run
```bash
gcloud run deploy patho-bot \
  --image gcr.io/$PROJECT_ID/patho-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars GOOGLE_API_KEY="your-gemini-api-key"
```

*   `--memory 2Gi`: Essential for loading the YOLO model and Agent.
*   `--allow-unauthenticated`: Makes the web app public.
*   `--set-env-vars`: **CRITICAL**. You must pass your Gemini API Key here so the container can access it.

## 4. Verification
1.  Open the URL provided by the deployment command.
2.  Enter a Patient ID (e.g., "TestUser").
3.  The app will connect to Firestore.
    *   *First run might be slightly slower as it initializes the connection.*
4.  Upload an image and run analysis.
5.  Refresh the page and load "TestUser" again. You should see the **History** loaded from the cloud!
