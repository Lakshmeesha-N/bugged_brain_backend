import os

# Set dummy environment variables for tests before Settings is instantiated
os.environ.setdefault("GCP_PROJECT_ID", "test-project-id")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
