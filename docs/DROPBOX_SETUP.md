# Dropbox OAuth 2.0 Setup Guide

This guide explains how to set up Dropbox integration using OAuth 2.0 with refresh tokens for PaperFlow.

## Why Refresh Tokens?

Starting September 30, 2021, Dropbox deprecated long-lived access tokens. All new apps must use short-lived access tokens (4 hours) with refresh tokens for security. The refresh token allows PaperFlow to automatically obtain new access tokens when they expire.

## Prerequisites

- A Dropbox account
- Python 3.11+ installed
- PaperFlow project set up locally

## Step-by-Step Setup

### 1. Create a Dropbox App

1. Go to https://www.dropbox.com/developers/apps
2. Click **"Create app"**
3. Choose:
   - **API**: Scoped access
   - **Access type**:
     - Choose "Full Dropbox" for access to all files
     - Or "App folder" for isolated folder access
4. **Name your app** (e.g., "PaperFlow")
5. Click **"Create app"**

### 2. Configure App Settings

1. In your app's settings page:
   - Note your **App key** (you'll need this)
   - Note your **App secret** (click "Show" to reveal it)

2. Under **"OAuth 2"** section:
   - **Token expiration**: Set to **"Short-lived"** (this ensures you get a refresh token)
   - **Redirect URIs**: Add `http://localhost` (or your preferred redirect URI)

3. Under **"Permissions"** tab:
   - Enable the following permissions:
     - `files.metadata.read`
     - `files.content.write`
     - `files.content.read`
     - `sharing.write` (for creating shared links)
   - Click **"Submit"** to save permissions

### 3. Obtain Refresh Token

#### Option A: Using the Helper Script (Recommended)

1. Run the helper script:
   ```bash
   python scripts/get_dropbox_refresh_token.py
   ```

2. Follow the interactive prompts:
   - Enter your App Key
   - Enter your App Secret
   - Authorize the app in your browser
   - Copy the authorization code from the redirect URL
   - Paste it into the script

3. The script will output your credentials in this format:
   ```
   DROPBOX_APP_KEY=your_app_key_here
   DROPBOX_APP_SECRET=your_app_secret_here
   DROPBOX_REFRESH_TOKEN=your_refresh_token_here
   ```

#### Option B: Manual Process

1. **Generate Authorization URL:**

   Replace `YOUR_APP_KEY` with your actual App Key:
   ```
   https://www.dropbox.com/oauth2/authorize?client_id=YOUR_APP_KEY&token_access_type=offline&response_type=code
   ```

   **Important:** The `token_access_type=offline` parameter is crucial for obtaining a refresh token.

2. **Authorize the App:**

   - Open the URL in your browser
   - Log in to Dropbox
   - Click "Allow" to authorize your app
   - You'll be redirected to a URL like: `http://localhost/?code=XXXXXXXXXX`
   - Copy the `code` parameter value (the authorization code)

3. **Exchange Code for Tokens:**

   Use curl or Python to exchange the authorization code for tokens:

   **Using curl:**
   ```bash
   curl -X POST https://api.dropboxapi.com/oauth2/token \
     -d code=YOUR_AUTHORIZATION_CODE \
     -d grant_type=authorization_code \
     -u YOUR_APP_KEY:YOUR_APP_SECRET
   ```

   **Using Python:**
   ```python
   import requests

   response = requests.post('https://api.dropboxapi.com/oauth2/token', data={
       'code': 'YOUR_AUTHORIZATION_CODE',
       'grant_type': 'authorization_code',
       'client_id': 'YOUR_APP_KEY',
       'client_secret': 'YOUR_APP_SECRET'
   })

   tokens = response.json()
   print(f"Refresh Token: {tokens['refresh_token']}")
   print(f"Access Token: {tokens['access_token']}")
   print(f"Expires in: {tokens['expires_in']} seconds")
   ```

4. **Save the Refresh Token:**

   From the response, copy the `refresh_token` value. This token never expires and will be used to obtain new access tokens automatically.

### 4. Configure PaperFlow

1. Copy `.env.example` to `.env` if you haven't already:
   ```bash
   cp .env.example .env
   ```

2. Add your Dropbox credentials to `.env`:
   ```bash
   DROPBOX_APP_KEY=your_app_key_here
   DROPBOX_APP_SECRET=your_app_secret_here
   DROPBOX_REFRESH_TOKEN=your_refresh_token_here
   DROPBOX_FOLDER_PATH=/PaperFlow
   ```

3. **Important:** Never commit your `.env` file to version control!

### 5. Verify Configuration

You can test your Dropbox configuration by running the test suite:

```bash
pytest tests/test_dropbox_connection.py -v
```

Or manually test by starting the application and attempting a PDF conversion with Dropbox upload enabled.

## How It Works

### Token Refresh Flow

1. **Initialization:** When PaperFlow starts, it uses the refresh token to obtain an initial access token
2. **Token Tracking:** The service tracks when the access token will expire (typically 4 hours)
3. **Automatic Refresh:** Before making any Dropbox API call, the service checks if the token is expired
4. **Seamless Renewal:** If expired, it automatically uses the refresh token to get a new access token
5. **No Interruption:** All this happens transparently without user intervention

### Security Considerations

- **Refresh tokens never expire** unless explicitly revoked
- Store refresh tokens securely (use environment variables, never hardcode)
- The access token is short-lived (4 hours) for better security
- If compromised, revoke the app's access from your Dropbox account settings

## Troubleshooting

### "Error 400: invalid_grant"

- Your authorization code has expired (valid for ~10 minutes)
- The code can only be used once
- Generate a new authorization URL and try again

### "Error: Missing refresh token or app credentials"

- Ensure all three environment variables are set:
  - `DROPBOX_APP_KEY`
  - `DROPBOX_APP_SECRET`
  - `DROPBOX_REFRESH_TOKEN`
- Check for typos or extra whitespace

### "Dropbox authentication failed"

- Verify your app has the correct permissions enabled
- Check that your refresh token hasn't been revoked
- Ensure your app is not in "Development" mode with expired test tokens

### Token Expiration Logs

You can monitor token refresh events in the application logs:
```
INFO: Access token refreshed successfully. Expires at: 2025-12-03 18:30:45+00:00
```

## Migration from Legacy Access Tokens

If you're currently using a long-lived access token (`DROPBOX_ACCESS_TOKEN`), the service will continue to work but you should migrate to refresh tokens:

1. Follow this guide to obtain a refresh token
2. Add the new OAuth credentials to your `.env` file
3. The service will automatically prefer the refresh token method
4. Once verified working, you can remove the old `DROPBOX_ACCESS_TOKEN`

## Additional Resources

- [Dropbox OAuth Guide](https://developers.dropbox.com/oauth-guide)
- [Dropbox API Documentation](https://www.dropbox.com/developers/documentation)
- [OAuth 2.0 Specification](https://oauth.net/2/)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review application logs for specific error messages
3. Verify your Dropbox app configuration
4. Open an issue on the PaperFlow GitHub repository
