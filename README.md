# Bioscope.AI LinkedIn Auto-Poster

Automated LinkedIn content posting system for Bioscope.AI's precision medicine educational content.

## Overview

This system automatically posts to LinkedIn 3x per week:
- **Sunday 8:00 AM MT** - Gene of the Week
- **Tuesday 8:00 AM MT** - Intervention of the Week  
- **Thursday 8:00 AM MT** - Health Topic of the Week

## How It Works

1. **GitHub Actions** triggers the workflow on schedule (Sun/Tue/Thu at 8am MT)
2. **Python script** reads today's content from `content/calendar.json`
3. **Claude API** generates fresh, engaging post text from structured content data
4. **LinkedIn API** uploads the image and publishes the post
5. **Logs** are saved for monitoring and debugging

## Setup Instructions

### 1. Fork/Clone This Repository

```bash
git clone https://github.com/bioscope-ai/linkedin-autoposter.git
cd linkedin-autoposter
```

### 2. Set Up LinkedIn API Access

You need a LinkedIn Page and API credentials:

#### A. Create a LinkedIn Company Page (if not already done)
- Go to linkedin.com/company/setup/new
- Create your Bioscope.AI company page

#### B. Create a LinkedIn Developer App
1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps)
2. Click "Create App"
3. Fill in:
   - App name: `Bioscope LinkedIn Poster`
   - LinkedIn Page: Select your Bioscope.AI page
   - App logo: Upload logo
4. Under "Products", request access to:
   - **Share on LinkedIn** (for posting)
   - **Sign In with LinkedIn using OpenID Connect**

#### C. Get Your Credentials
1. Go to your app's "Auth" tab
2. Copy:
   - **Client ID**
   - **Client Secret**
3. Add OAuth 2.0 Redirect URL: `http://localhost:8000/callback`

#### D. Generate Access Token
Run the included helper script locally:

```bash
pip install -r requirements.txt
python scripts/get_linkedin_token.py
```

This will:
1. Open a browser for LinkedIn authorization
2. Generate a 60-day access token
3. Display your Organization ID

**Note:** LinkedIn access tokens expire after 60 days. Set a calendar reminder to refresh, or use the refresh token flow.

### 3. Set Up Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Copy the key (starts with `sk-ant-`)

### 4. Configure GitHub Secrets

In your GitHub repo, go to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Value |
|-------------|-------|
| `LINKEDIN_ACCESS_TOKEN` | Your LinkedIn OAuth access token |
| `LINKEDIN_ORG_ID` | Your LinkedIn Organization/Company ID |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (sk-ant-...) |

### 5. Upload Content Images

All 156 images should be in the `content/images/` directory with naming convention:
```
week{N}_{day}_{topic}.jpg

Examples:
week1_sun_comt.jpg
week1_tue_nmn.jpg
week1_thu_cgm.jpg
```

### 6. Test the System

Manually trigger a test run:

```bash
# Local test (dry run - won't actually post)
python post_to_linkedin.py --dry-run

# Or trigger via GitHub Actions
# Go to Actions tab → "LinkedIn Post" → "Run workflow"
```

### 7. Enable the Schedule

The workflow is enabled by default. Posts will automatically publish at:
- Sunday 3:00 PM UTC (8:00 AM MT)
- Tuesday 3:00 PM UTC (8:00 AM MT)
- Thursday 3:00 PM UTC (8:00 AM MT)

## File Structure

```
bioscope-linkedin-autoposter/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── post_to_linkedin.py          # Main posting script
├── config.py                    # Configuration settings
├── content/
│   ├── calendar.json            # 156 scheduled posts with content data
│   └── images/                  # All 156 post images (1080x1080 JPG)
│       ├── week1_sun_comt.jpg
│       ├── week1_tue_nmn.jpg
│       └── ...
├── scripts/
│   ├── get_linkedin_token.py    # Helper to get LinkedIn OAuth token
│   └── refresh_token.py         # Refresh expired tokens
├── templates/
│   └── system_prompt.txt        # Claude system prompt for text generation
├── .github/
│   └── workflows/
│       └── post.yml             # GitHub Actions workflow
└── logs/                        # Post logs (gitignored)
```

## Content Calendar

The `content/calendar.json` file contains all 156 posts with:
- Scheduled date
- Post type (gene/intervention/topic)
- Structured content data
- Image filename
- References

To modify content, edit the JSON file and commit changes.

## Monitoring

### View Post History
Check the GitHub Actions tab to see:
- When each post was published
- Success/failure status
- Full logs

### Notifications
To get notified of failures, add a Slack webhook:
1. Create a Slack incoming webhook
2. Add `SLACK_WEBHOOK_URL` to GitHub secrets
3. Uncomment the notification step in `.github/workflows/post.yml`

## Troubleshooting

### "LinkedIn token expired"
Run `python scripts/refresh_token.py` or `scripts/get_linkedin_token.py` to get a new token, then update the GitHub secret.

### "Image upload failed"
- Ensure image is JPG format
- Check file size is under 8MB
- Verify image exists at expected path

### "Post not appearing"
- Check LinkedIn Page admin access
- Verify Organization ID is correct
- Check for LinkedIn API rate limits

## Customization

### Change Posting Times
Edit `.github/workflows/post.yml`:
```yaml
schedule:
  - cron: '0 15 * * 0'  # Sunday 3pm UTC = 8am MT
```

### Modify Text Generation
Edit `templates/system_prompt.txt` to adjust Claude's writing style.

### Add New Content
1. Add entry to `content/calendar.json`
2. Add image to `content/images/`
3. Commit and push

## License

Proprietary - Bioscope.AI
