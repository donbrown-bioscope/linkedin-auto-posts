#!/usr/bin/env python3
"""
LinkedIn OAuth Token Generator

This script helps you obtain a LinkedIn access token for the auto-poster.
Run this locally when you need to get or refresh your token.

Usage:
    python get_linkedin_token.py

Requirements:
    1. Create a LinkedIn Developer App at https://www.linkedin.com/developers/apps
    2. Add http://localhost:8000/callback as an OAuth 2.0 redirect URL
    3. Request access to "Share on LinkedIn" product
    4. Set environment variables or enter when prompted:
       - LINKEDIN_CLIENT_ID
       - LINKEDIN_CLIENT_SECRET
"""

import os
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
import requests
from flask import Flask, request

app = Flask(__name__)

# Configuration
CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8000/callback"
# Scopes for posting to personal profile
SCOPES = ["w_member_social"]

# Global to store the auth code
auth_code = None


def get_authorization_url():
    """Generate the LinkedIn OAuth authorization URL."""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "bioscope_linkedin_auth"
    }
    return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token."""
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None
    
    return response.json()


def get_user_info(access_token: str) -> dict:
    """Get the authenticated user's profile info."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    return response.json() if response.status_code == 200 else None


def get_organization_info(access_token: str) -> list:
    """Get organizations the user can post to."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    # Get organization access control
    response = requests.get(
        "https://api.linkedin.com/v2/organizationAcls?q=roleAssignee",
        headers=headers
    )
    
    if response.status_code != 200:
        return []
    
    return response.json().get("elements", [])


@app.route("/callback")
def callback():
    """Handle the OAuth callback from LinkedIn."""
    global auth_code
    
    error = request.args.get("error")
    if error:
        return f"Error: {error} - {request.args.get('error_description', '')}"
    
    auth_code = request.args.get("code")
    
    return """
    <html>
        <body>
            <h1>✅ Authorization successful!</h1>
            <p>You can close this window and return to the terminal.</p>
            <script>window.close();</script>
        </body>
    </html>
    """


def main():
    global CLIENT_ID, CLIENT_SECRET
    
    print("=" * 60)
    print("LinkedIn OAuth Token Generator for Bioscope.AI")
    print("=" * 60)
    print()
    
    # Get credentials if not set
    if not CLIENT_ID:
        CLIENT_ID = input("Enter your LinkedIn Client ID: ").strip()
    if not CLIENT_SECRET:
        CLIENT_SECRET = input("Enter your LinkedIn Client Secret: ").strip()
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Client ID and Secret are required")
        return
    
    print()
    print("Opening browser for LinkedIn authorization...")
    print("(If browser doesn't open, copy this URL manually)")
    print()
    
    auth_url = get_authorization_url()
    print(auth_url)
    print()
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    print("Waiting for authorization callback...")
    print("(Local server running on http://localhost:8000)")
    print()
    
    # Run Flask server briefly to catch the callback
    import threading
    import time
    
    server_thread = threading.Thread(target=lambda: app.run(port=8000, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for auth code
    timeout = 120  # 2 minutes
    start = time.time()
    while auth_code is None and (time.time() - start) < timeout:
        time.sleep(1)
    
    if auth_code is None:
        print("Timeout waiting for authorization")
        return
    
    print("Received authorization code!")
    print("Exchanging for access token...")
    print()
    
    token_data = exchange_code_for_token(auth_code)
    
    if not token_data:
        print("Failed to get access token")
        return
    
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 0)
    
    print("=" * 60)
    print("SUCCESS! Here are your credentials:")
    print("=" * 60)
    print()
    print(f"ACCESS TOKEN (save this as LINKEDIN_ACCESS_TOKEN):")
    print(f"{access_token}")
    print()
    print(f"Token expires in: {expires_in // 86400} days")
    print()
    
    # Get user info
    user_info = get_user_info(access_token)
    if user_info:
        print(f"Authenticated as: {user_info.get('name', 'Unknown')}")
        print(f"Email: {user_info.get('email', 'Unknown')}")
        print()
    
    # Get organization info
    print("Checking organization access...")
    orgs = get_organization_info(access_token)
    
    if orgs:
        print()
        print("Organizations you can post to:")
        for org in orgs:
            org_urn = org.get("organization", "")
            org_id = org_urn.split(":")[-1] if org_urn else "Unknown"
            role = org.get("role", "Unknown")
            print(f"  - Organization ID: {org_id} (Role: {role})")
        print()
        print("Save the Organization ID as LINKEDIN_ORG_ID")
    else:
        print("No organization access found.")
        print("Make sure your LinkedIn app has organization posting permissions.")
    
    print()
    print("=" * 60)
    print("Next steps:")
    print("1. Add LINKEDIN_ACCESS_TOKEN to your GitHub secrets")
    print("2. Add LINKEDIN_ORG_ID to your GitHub secrets")
    print(f"3. Set a reminder to refresh token in {expires_in // 86400} days")
    print("=" * 60)


if __name__ == "__main__":
    main()
