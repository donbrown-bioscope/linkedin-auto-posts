"""
Configuration settings for Bioscope LinkedIn Auto-Poster
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content"
IMAGES_DIR = CONTENT_DIR / "images"
LOGS_DIR = BASE_DIR / "logs"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)

# LinkedIn API Configuration (loaded from environment variables)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN")

# For personal profile posting, we need the person URN (not org ID)
# This will be fetched automatically using the access token
LINKEDIN_PERSON_ID = os.environ.get("LINKEDIN_PERSON_ID")

# Optional: Slack notifications
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# LinkedIn API endpoints
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
LINKEDIN_UPLOAD_URL = f"{LINKEDIN_API_BASE}/assets?action=registerUpload"
LINKEDIN_POSTS_URL = f"{LINKEDIN_API_BASE}/posts"

# Claude model for text generation
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Posting schedule (for reference - actual schedule in GitHub Actions)
POSTING_DAYS = {
    "sunday": "gene",
    "tuesday": "intervention",
    "thursday": "topic"
}

# Timezone for logging
TIMEZONE = "America/Denver"  # Mountain Time

# Post settings
MAX_POST_LENGTH = 3000  # LinkedIn character limit
IMAGE_MAX_SIZE_MB = 8

# Hashtag sets by post type
HASHTAGS = {
    "gene": "#GeneOfTheWeek #Genetics #PrecisionMedicine #PersonalizedHealth #Bioscope",
    "intervention": "#InterventionOfTheWeek #Longevity #AntiAging #PrecisionMedicine #Bioscope",
    "topic": "#HealthTopic #Prevention #PrecisionHealth #Diagnostics #Bioscope"
}

# CTA templates
PHYSICIAN_CTA = "👨‍⚕️ Physicians: Why aren't you using Bioscope.AI to offer true AI-powered precision medicine?"
PATIENT_CTA = "🧑 Patients: Why isn't your physician using Bioscope.AI to maximize your healthy longevity?"
