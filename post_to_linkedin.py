#!/usr/bin/env python3
"""
Bioscope.AI LinkedIn Auto-Poster

This script:
1. Determines what content to post based on today's date
2. Generates engaging post text using Claude
3. Uploads the image and publishes to LinkedIn
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, date
from pathlib import Path

import requests
import anthropic

import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOGS_DIR / f"post_{date.today().isoformat()}.log")
    ]
)
logger = logging.getLogger(__name__)


def load_calendar() -> list:
    """Load the content calendar from JSON file."""
    calendar_path = config.CONTENT_DIR / "calendar.json"
    with open(calendar_path, 'r') as f:
        return json.load(f)


def get_todays_post(calendar: list, target_date: date = None) -> dict | None:
    """
    Find the post scheduled for today (or target_date if specified).
    Returns None if no post is scheduled.
    """
    if target_date is None:
        target_date = date.today()
    
    target_str = target_date.isoformat()
    
    for post in calendar:
        if post.get('date') == target_str:
            return post
    
    return None


def load_system_prompt() -> str:
    """Load the Claude system prompt for text generation."""
    prompt_path = config.TEMPLATES_DIR / "system_prompt.txt"
    with open(prompt_path, 'r') as f:
        return f.read()


def generate_post_text(post_data: dict, client: anthropic.Anthropic) -> str:
    """
    Generate engaging LinkedIn post text using Claude.
    """
    system_prompt = load_system_prompt()
    
    user_prompt = f"""Generate a LinkedIn post for the following content:

Post Type: {post_data['post_type']}
Week: {post_data['week']}

Content Data:
{json.dumps(post_data['content_data'], indent=2)}

Remember to:
1. Start with an engaging hook
2. Use the emoji appropriate for the post type (🧬 for gene, 💊 for intervention, 📊 for topic)
3. Include key information in an accessible way
4. End with the dual CTA for physicians and patients
5. Add relevant hashtags
6. Keep under 3000 characters total
"""

    logger.info("Generating post text with Claude...")
    
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    generated_text = response.content[0].text
    logger.info(f"Generated {len(generated_text)} characters of post text")
    
    return generated_text


def get_person_urn(access_token: str) -> str:
    """Get the authenticated user's LinkedIn person URN."""
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    
    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get user info: {response.text}")
        raise Exception(f"Failed to get LinkedIn user info: {response.status_code}")
    
    data = response.json()
    person_id = data.get("sub")  # 'sub' contains the person ID
    logger.info(f"Authenticated as: {data.get('name', 'Unknown')}")
    
    return f"urn:li:person:{person_id}"


def upload_image_to_linkedin(image_path: Path, access_token: str, person_urn: str) -> str:
    """
    Upload an image to LinkedIn and return the asset URN.
    
    LinkedIn image upload is a 2-step process:
    1. Register the upload and get an upload URL
    2. Upload the binary image data
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    # Step 1: Register the upload
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
    
    logger.info("Registering image upload with LinkedIn...")
    
    register_response = requests.post(
        config.LINKEDIN_UPLOAD_URL,
        headers=headers,
        json=register_payload
    )
    
    if register_response.status_code != 200:
        logger.error(f"Failed to register upload: {register_response.text}")
        raise Exception(f"LinkedIn upload registration failed: {register_response.status_code}")
    
    register_data = register_response.json()
    upload_url = register_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = register_data["value"]["asset"]
    
    # Step 2: Upload the image binary
    logger.info(f"Uploading image: {image_path}")
    
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
    
    upload_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "image/jpeg",
    }
    
    upload_response = requests.put(
        upload_url,
        headers=upload_headers,
        data=image_data
    )
    
    if upload_response.status_code not in [200, 201]:
        logger.error(f"Failed to upload image: {upload_response.text}")
        raise Exception(f"LinkedIn image upload failed: {upload_response.status_code}")
    
    logger.info(f"Image uploaded successfully. Asset URN: {asset_urn}")
    return asset_urn


def create_linkedin_post(text: str, image_asset_urn: str, access_token: str, person_urn: str) -> dict:
    """
    Create a LinkedIn post with text and image.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    post_payload = {
        "author": person_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "title": "Bioscope.AI",
                "id": image_asset_urn
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    
    logger.info("Creating LinkedIn post...")
    
    response = requests.post(
        config.LINKEDIN_POSTS_URL,
        headers=headers,
        json=post_payload
    )
    
    if response.status_code not in [200, 201]:
        logger.error(f"Failed to create post: {response.text}")
        raise Exception(f"LinkedIn post creation failed: {response.status_code}")
    
    result = response.json()
    logger.info(f"Post created successfully!")
    
    return result


def send_slack_notification(message: str, success: bool = True):
    """Send a notification to Slack (if configured)."""
    if not config.SLACK_WEBHOOK_URL:
        return
    
    emoji = "✅" if success else "❌"
    payload = {
        "text": f"{emoji} {message}",
        "username": "Bioscope LinkedIn Bot"
    }
    
    try:
        requests.post(config.SLACK_WEBHOOK_URL, json=payload)
    except Exception as e:
        logger.warning(f"Failed to send Slack notification: {e}")


def main():
    parser = argparse.ArgumentParser(description="Bioscope LinkedIn Auto-Poster")
    parser.add_argument("--dry-run", action="store_true", help="Generate content but don't post")
    parser.add_argument("--date", type=str, help="Override date (YYYY-MM-DD format)")
    parser.add_argument("--force", action="store_true", help="Post even if not a scheduled day")
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today()
    
    day_name = target_date.strftime("%A").lower()
    logger.info(f"Running for date: {target_date} ({day_name})")
    
    # Check if today is a posting day
    if day_name not in config.POSTING_DAYS and not args.force:
        logger.info(f"Today ({day_name}) is not a scheduled posting day. Exiting.")
        return
    
    # Validate configuration
    if not args.dry_run:
        if not config.LINKEDIN_ACCESS_TOKEN:
            logger.error("LINKEDIN_ACCESS_TOKEN not set")
            sys.exit(1)
    
    if not config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    # Load calendar and find today's post
    calendar = load_calendar()
    post = get_todays_post(calendar, target_date)
    
    if not post:
        logger.warning(f"No post scheduled for {target_date}")
        return
    
    logger.info(f"Found scheduled post: Week {post['week']} - {post['post_type']} - {post.get('title', 'Untitled')}")
    
    # Initialize Claude client
    claude = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    
    # Generate post text
    post_text = generate_post_text(post, claude)
    
    logger.info("=" * 50)
    logger.info("GENERATED POST TEXT:")
    logger.info("=" * 50)
    logger.info(post_text)
    logger.info("=" * 50)
    
    if args.dry_run:
        logger.info("DRY RUN - Not posting to LinkedIn")
        return
    
    # Get image path
    image_filename = post.get('image_file')
    if not image_filename:
        logger.error("No image_file specified in post data")
        sys.exit(1)
    
    image_path = config.IMAGES_DIR / image_filename
    if not image_path.exists():
        logger.error(f"Image not found: {image_path}")
        sys.exit(1)
    
    try:
        # Get person URN from access token
        person_urn = get_person_urn(config.LINKEDIN_ACCESS_TOKEN)
        
        # Upload image
        asset_urn = upload_image_to_linkedin(
            image_path,
            config.LINKEDIN_ACCESS_TOKEN,
            person_urn
        )
        
        # Create post
        result = create_linkedin_post(
            post_text,
            asset_urn,
            config.LINKEDIN_ACCESS_TOKEN,
            person_urn
        )
        
        # Log success
        logger.info(f"Successfully posted: Week {post['week']} {post['post_type']}")
        send_slack_notification(
            f"Posted Week {post['week']} {post['post_type']}: {post.get('title', 'Untitled')}"
        )
        
        # Save post ID to calendar (for tracking)
        # In production, you'd update a database or the JSON file
        
    except Exception as e:
        logger.error(f"Failed to post: {e}")
        send_slack_notification(f"FAILED to post Week {post['week']}: {e}", success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
