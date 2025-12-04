#!/usr/bin/env python3
"""
Helper script to obtain Dropbox refresh token for OAuth 2.0 authentication.

This script guides you through the OAuth flow to get a refresh token.
"""

import webbrowser
import requests
from urllib.parse import urlencode


def get_refresh_token():
    """Guide user through OAuth flow to obtain refresh token."""
    print("=" * 70)
    print("Dropbox OAuth 2.0 Refresh Token Generator")
    print("=" * 70)
    print()

    # Get app credentials
    print("First, you need to create a Dropbox app:")
    print("1. Go to https://www.dropbox.com/developers/apps")
    print("2. Click 'Create app'")
    print("3. Choose 'Scoped access'")
    print("4. Choose the access level (Full Dropbox or App folder)")
    print("5. Name your app")
    print()

    app_key = input("Enter your App Key: ").strip()
    app_secret = input("Enter your App Secret: ").strip()

    if not app_key or not app_secret:
        print("Error: App Key and App Secret are required!")
        return

    print()
    print("-" * 70)
    print("Step 1: Authorization")
    print("-" * 70)
    print()
    print("IMPORTANT: Before continuing, ensure your app settings have:")
    print("  - Token expiration set to 'Short-lived'")
    print("  - A redirect URI configured (use http://localhost for this script)")
    print()

    # Build authorization URL
    params = {
        'client_id': app_key,
        'response_type': 'code',
        'token_access_type': 'offline'  # This requests a refresh token
    }
    auth_url = f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"

    print("Opening authorization URL in your browser...")
    print(f"URL: {auth_url}")
    print()

    try:
        webbrowser.open(auth_url)
    except Exception:
        print("Could not open browser automatically. Please open the URL manually.")

    print("After authorizing the app, you'll be redirected to a URL like:")
    print("http://localhost/?code=XXXXXXXXXXXXXXXXXX")
    print()

    auth_code = input("Paste the authorization code from the URL: ").strip()

    if not auth_code:
        print("Error: Authorization code is required!")
        return

    print()
    print("-" * 70)
    print("Step 2: Exchanging code for tokens")
    print("-" * 70)
    print()

    # Exchange authorization code for tokens
    try:
        response = requests.post(
            'https://api.dropboxapi.com/oauth2/token',
            data={
                'code': auth_code,
                'grant_type': 'authorization_code',
                'client_id': app_key,
                'client_secret': app_secret
            }
        )

        if response.status_code == 200:
            tokens = response.json()

            print("✓ Success! Here are your tokens:")
            print()
            print("=" * 70)
            print("SAVE THESE VALUES IN YOUR .env FILE:")
            print("=" * 70)
            print(f"DROPBOX_APP_KEY={app_key}")
            print(f"DROPBOX_APP_SECRET={app_secret}")
            print(f"DROPBOX_REFRESH_TOKEN={tokens['refresh_token']}")
            print("=" * 70)
            print()
            print("Additional information:")
            print(f"  Access Token (expires in {tokens.get('expires_in', 0)} seconds):")
            print(f"    {tokens['access_token'][:20]}...")
            print(f"  Refresh Token (never expires):")
            print(f"    {tokens['refresh_token'][:20]}...")
            print()
            print("NOTE: The refresh token never expires and will be used to")
            print("      automatically obtain new access tokens when needed.")

        else:
            print(f"Error: Failed to exchange code for tokens")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    get_refresh_token()
