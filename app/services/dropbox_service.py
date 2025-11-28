"""Dropbox integration service for PDF upload."""

import os
import httpx
from typing import Optional
from dropbox import Dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from app.core.config import settings


class DropboxService:
    """Service for uploading PDFs to Dropbox with automatic token refresh."""

    def __init__(self):
        self.access_token = settings.DROPBOX_ACCESS_TOKEN
        self.refresh_token = settings.DROPBOX_REFRESH_TOKEN
        self.app_key = settings.DROPBOX_APP_KEY
        self.app_secret = settings.DROPBOX_APP_SECRET
        self.folder_path = settings.DROPBOX_FOLDER_PATH
        self.client: Optional[Dropbox] = None

        if self.access_token:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize Dropbox client."""
        try:
            self.client = Dropbox(self.access_token)
            # Verify that the token is valid
            self.client.users_get_current_account()
        except AuthError as e:
            # Try to refresh token if refresh token is available
            if self.refresh_token and self.app_key and self.app_secret:
                if self._refresh_access_token():
                    self._initialize_client()
                    return
            raise Exception(f"Dropbox authentication failed: {str(e)}")

    def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.

        Returns:
            True if successful, False otherwise
        """
        if not (self.refresh_token and self.app_key and self.app_secret):
            return False

        try:
            url = "https://api.dropboxapi.com/oauth2/token"
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.app_key,
                "client_secret": self.app_secret,
            }

            response = httpx.post(url, data=payload, timeout=30.0)
            response.raise_for_status()

            data = response.json()
            if "access_token" in data:
                self.access_token = data["access_token"]
                return True
            return False

        except Exception as e:
            print(f"Token refresh failed: {str(e)}")
            return False

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
                "Dropbox client not initialized. Please configure DROPBOX_ACCESS_TOKEN."
            )

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
            # Token expired, try to refresh
            if self._refresh_access_token():
                self._initialize_client()
                return await self.upload_file(local_path, remote_filename)
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

        if not folder_path:
            folder_path = self.folder_path

        try:
            # Try to get folder metadata
            self.client.files_get_metadata(folder_path)
        except AuthError as e:
            # Token expired, try to refresh
            if self._refresh_access_token():
                self._initialize_client()
                return await self.create_folder_if_not_exists(folder_path)
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
