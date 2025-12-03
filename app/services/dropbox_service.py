"""Dropbox integration service for PDF upload."""

import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional
from dropbox import Dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from app.core.config import settings


class DropboxService:
    """Service for uploading PDFs to Dropbox using OAuth 2.0 refresh tokens."""

    def __init__(self):
        # OAuth 2.0 credentials
        self.app_key = settings.DROPBOX_APP_KEY
        self.app_secret = settings.DROPBOX_APP_SECRET
        self.refresh_token = settings.DROPBOX_REFRESH_TOKEN

        # Legacy access token (for backwards compatibility)
        self.access_token = settings.DROPBOX_ACCESS_TOKEN

        # Token expiration tracking
        self.token_expires_at: Optional[datetime] = None

        self.folder_path = settings.DROPBOX_FOLDER_PATH
        self.client: Optional[Dropbox] = None

        # Initialize client with available credentials
        if self.refresh_token and self.app_key and self.app_secret:
            self._initialize_client_with_refresh_token()
        elif self.access_token:
            self._initialize_client_with_access_token()

    def _initialize_client_with_refresh_token(self):
        """Initialize Dropbox client using refresh token."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Get initial access token from refresh token
            self._refresh_access_token()

            if self.access_token:
                self.client = Dropbox(self.access_token)
                # Verify that the token is valid
                self.client.users_get_current_account()
                logger.info("Dropbox client initialized successfully with refresh token.")
        except Exception as e:
            logger.warning(f"Dropbox authentication failed: {str(e)}. Dropbox upload will be disabled.")
            self.client = None

    def _initialize_client_with_access_token(self):
        """Initialize Dropbox client using legacy access token."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            self.client = Dropbox(self.access_token)
            # Verify that the token is valid
            self.client.users_get_current_account()
            logger.info("Dropbox client initialized successfully with access token.")
        except AuthError as e:
            logger.warning(f"Dropbox authentication failed: {str(e)}. Dropbox upload will be disabled.")
            self.client = None

    def _refresh_access_token(self):
        """
        Refresh the access token using the refresh token.

        Returns:
            bool: True if token was refreshed successfully, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self.refresh_token or not self.app_key or not self.app_secret:
            logger.error("Missing refresh token or app credentials")
            return False

        try:
            response = requests.post(
                'https://api.dropboxapi.com/oauth2/token',
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
                    'client_id': self.app_key,
                    'client_secret': self.app_secret
                }
            )

            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens['access_token']
                expires_in = tokens.get('expires_in', 14400)  # Default 4 hours

                # Set expiration time with 5-minute buffer for safety
                self.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 300)

                # Update the client with new token
                if self.client:
                    self.client = Dropbox(self.access_token)

                logger.info(f"Access token refreshed successfully. Expires at: {self.token_expires_at}")
                return True
            else:
                logger.error(f"Failed to refresh access token: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return False

    def _ensure_valid_token(self):
        """
        Ensure the access token is valid, refreshing if necessary.

        Returns:
            bool: True if token is valid, False otherwise
        """
        # If using legacy access token (no refresh token), assume it's valid
        if not self.refresh_token:
            return self.access_token is not None

        # Check if token is expired or about to expire
        if self.token_expires_at is None or datetime.now(timezone.utc) >= self.token_expires_at:
            return self._refresh_access_token()

        return True

    async def upload_file(
        self, local_path: str, remote_filename: Optional[str] = None
    ) -> str:
        """
        Upload a file to Dropbox.

        Args:
            local_path: Path to local file
            remote_filename: Optional custom filename for Dropbox (uses local filename if not provided)

        Returns:
            Dropbox path to uploaded file

        Raises:
            Exception: If upload fails or client not initialized
        """
        if not self.client:
            raise Exception(
                "Dropbox client not initialized. Please configure Dropbox credentials."
            )

        # Ensure token is valid before making API call
        if not self._ensure_valid_token():
            raise Exception("Failed to obtain valid Dropbox access token.")

        if not os.path.exists(local_path):
            raise Exception(f"Local file not found: {local_path}")

        try:
            # Determine remote filename
            if not remote_filename:
                remote_filename = os.path.basename(local_path)

            # Construct full Dropbox path
            dropbox_path = f"{self.folder_path}/{remote_filename}"

            # Ensure folder path doesn't have double slashes
            dropbox_path = dropbox_path.replace("//", "/")

            # Read file content
            with open(local_path, "rb") as f:
                file_data = f.read()

            # Upload file to Dropbox
            # Using WriteMode.overwrite to replace existing files with same name
            self.client.files_upload(
                file_data, dropbox_path, mode=WriteMode("overwrite"), mute=True
            )

            return dropbox_path

        except AuthError as e:
            raise Exception(f"Dropbox authentication failed: {str(e)}")
        except ApiError as e:
            raise Exception(f"Dropbox API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to upload file to Dropbox: {str(e)}")

    async def create_folder_if_not_exists(self, folder_path: Optional[str] = None):
        """
        Create a folder in Dropbox if it doesn't exist.

        Args:
            folder_path: Path to folder (uses configured folder if not provided)
        """
        if not self.client:
            raise Exception("Dropbox client not initialized")

        # Ensure token is valid before making API call
        if not self._ensure_valid_token():
            raise Exception("Failed to obtain valid Dropbox access token.")

        if not folder_path:
            folder_path = self.folder_path

        try:
            # Try to get folder metadata
            self.client.files_get_metadata(folder_path)
        except AuthError as e:
            raise Exception(f"Dropbox authentication failed: {str(e)}")
        except ApiError as e:
            # If folder doesn't exist, create it
            if e.error.is_path() and e.error.get_path().is_not_found():
                try:
                    self.client.files_create_folder_v2(folder_path)
                except ApiError:
                    # Folder might have been created by another process
                    pass
            else:
                raise Exception(f"Error checking/creating folder: {str(e)}")

    def is_configured(self) -> bool:
        """Check if Dropbox is properly configured."""
        return self.client is not None

    async def get_shared_link(self, dropbox_path: str) -> Optional[str]:
        """
        Get or create a shared link for a file.

        Args:
            dropbox_path: Path to file in Dropbox

        Returns:
            Shared link URL or None if failed
        """
        if not self.client:
            return None

        # Ensure token is valid before making API call
        if not self._ensure_valid_token():
            return None

        try:
            # Try to get existing shared links
            links = self.client.sharing_list_shared_links(path=dropbox_path)
            if links.links:
                return links.links[0].url

            # Create new shared link
            link = self.client.sharing_create_shared_link_with_settings(
                dropbox_path
            )
            return link.url
        except ApiError:
            # Return None if we can't create a shared link
            return None
