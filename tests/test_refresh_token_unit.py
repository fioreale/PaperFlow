"""Unit tests for Dropbox refresh token mechanism with mocked API responses.

These tests don't require real Dropbox credentials - they mock the API responses
to test error handling and edge cases.

Usage:
    uv run pytest tests/test_refresh_token_unit.py -v
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_settings():
    """Mock settings with refresh token credentials."""
    with patch('app.services.dropbox_service.settings') as mock:
        mock.DROPBOX_APP_KEY = "test_app_key"
        mock.DROPBOX_APP_SECRET = "test_app_secret"
        mock.DROPBOX_REFRESH_TOKEN = "test_refresh_token"
        mock.DROPBOX_ACCESS_TOKEN = None
        mock.DROPBOX_FOLDER_PATH = "/TestFolder"
        yield mock


@pytest.fixture
def mock_successful_token_response():
    """Mock a successful token refresh response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'access_token': 'new_access_token_12345',
        'expires_in': 14400  # 4 hours
    }
    return mock_response


class TestRefreshTokenSuccess:
    """Tests for successful token refresh scenarios."""

    def test_refresh_token_returns_true_on_success(self, mock_settings, mock_successful_token_response):
        """Test that _refresh_access_token returns True on successful refresh."""
        with patch('app.services.dropbox_service.requests.post', return_value=mock_successful_token_response):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                # Create service without auto-initialization
                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "test_app_key"
                    service.app_secret = "test_app_secret"
                    service.refresh_token = "test_refresh_token"

                    result = service._refresh_access_token()

                    assert result is True
                    assert service.access_token == 'new_access_token_12345'
                    assert service.token_expires_at is not None

    def test_token_expiration_set_with_buffer(self, mock_settings, mock_successful_token_response):
        """Test that token expiration is set with 5-minute safety buffer."""
        with patch('app.services.dropbox_service.requests.post', return_value=mock_successful_token_response):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "test_app_key"
                    service.app_secret = "test_app_secret"
                    service.refresh_token = "test_refresh_token"

                    before = datetime.now(timezone.utc)
                    service._refresh_access_token()
                    after = datetime.now(timezone.utc)

                    # expires_in is 14400 (4 hours), minus 300 (5 min buffer) = 14100 seconds
                    expected_min = before + timedelta(seconds=14100 - 1)
                    expected_max = after + timedelta(seconds=14100 + 1)

                    assert expected_min <= service.token_expires_at <= expected_max


class TestRefreshTokenFailure:
    """Tests for token refresh failure scenarios."""

    def test_refresh_with_invalid_token(self, mock_settings):
        """Test handling of invalid/revoked refresh token (400 response)."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid_grant: refresh token is invalid or revoked"

        with patch('app.services.dropbox_service.requests.post', return_value=mock_response):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "test_app_key"
                    service.app_secret = "test_app_secret"
                    service.refresh_token = "invalid_token"

                    result = service._refresh_access_token()

                    assert result is False

    def test_refresh_with_network_error(self, mock_settings):
        """Test handling of network errors during token refresh."""
        import requests

        with patch('app.services.dropbox_service.requests.post', side_effect=requests.exceptions.ConnectionError("Network unreachable")):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "test_app_key"
                    service.app_secret = "test_app_secret"
                    service.refresh_token = "test_refresh_token"

                    result = service._refresh_access_token()

                    assert result is False

    def test_refresh_with_timeout(self, mock_settings):
        """Test handling of timeout during token refresh."""
        import requests

        with patch('app.services.dropbox_service.requests.post', side_effect=requests.exceptions.Timeout("Request timed out")):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "test_app_key"
                    service.app_secret = "test_app_secret"
                    service.refresh_token = "test_refresh_token"

                    result = service._refresh_access_token()

                    assert result is False

    def test_refresh_with_server_error(self, mock_settings):
        """Test handling of Dropbox server errors (500 response)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch('app.services.dropbox_service.requests.post', return_value=mock_response):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "test_app_key"
                    service.app_secret = "test_app_secret"
                    service.refresh_token = "test_refresh_token"

                    result = service._refresh_access_token()

                    assert result is False


class TestEnsureValidToken:
    """Tests for _ensure_valid_token method."""

    def test_ensure_valid_token_with_valid_token(self, mock_settings, mock_successful_token_response):
        """Test that valid token doesn't trigger refresh."""
        with patch('app.services.dropbox_service.requests.post', return_value=mock_successful_token_response):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.refresh_token = "test_refresh_token"
                    service.access_token = "valid_token"
                    service.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=2)

                    with patch.object(service, '_refresh_access_token') as mock_refresh:
                        result = service._ensure_valid_token()

                        assert result is True
                        mock_refresh.assert_not_called()

    def test_ensure_valid_token_triggers_refresh_when_expired(self, mock_settings, mock_successful_token_response):
        """Test that expired token triggers refresh."""
        with patch('app.services.dropbox_service.requests.post', return_value=mock_successful_token_response):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "test_app_key"
                    service.app_secret = "test_app_secret"
                    service.refresh_token = "test_refresh_token"
                    service.access_token = "expired_token"
                    service.token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)

                    result = service._ensure_valid_token()

                    assert result is True
                    assert service.access_token == 'new_access_token_12345'

    def test_ensure_valid_token_with_no_expiry_set(self, mock_settings, mock_successful_token_response):
        """Test that None expiry triggers refresh."""
        with patch('app.services.dropbox_service.requests.post', return_value=mock_successful_token_response):
            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "test_app_key"
                    service.app_secret = "test_app_secret"
                    service.refresh_token = "test_refresh_token"
                    service.access_token = "some_token"
                    service.token_expires_at = None  # Expiry not set

                    result = service._ensure_valid_token()

                    assert result is True
                    assert service.access_token == 'new_access_token_12345'


class TestLegacyAccessToken:
    """Tests for legacy access token support."""

    def test_legacy_token_no_refresh_needed(self):
        """Test that legacy access token doesn't try to refresh."""
        with patch('app.services.dropbox_service.settings') as mock_settings:
            mock_settings.DROPBOX_APP_KEY = None
            mock_settings.DROPBOX_APP_SECRET = None
            mock_settings.DROPBOX_REFRESH_TOKEN = None
            mock_settings.DROPBOX_ACCESS_TOKEN = "legacy_access_token"
            mock_settings.DROPBOX_FOLDER_PATH = "/TestFolder"

            with patch('app.services.dropbox_service.Dropbox') as mock_dropbox:
                mock_client = MagicMock()
                mock_dropbox.return_value = mock_client

                from app.services.dropbox_service import DropboxService

                service = DropboxService()

                # _ensure_valid_token should return True without trying to refresh
                result = service._ensure_valid_token()

                assert result is True
                assert service.refresh_token is None


class TestMissingCredentials:
    """Tests for missing credential scenarios."""

    def test_refresh_fails_without_app_key(self):
        """Test that refresh fails when app_key is missing."""
        with patch('app.services.dropbox_service.settings') as mock_settings:
            mock_settings.DROPBOX_APP_KEY = None
            mock_settings.DROPBOX_APP_SECRET = "secret"
            mock_settings.DROPBOX_REFRESH_TOKEN = "token"
            mock_settings.DROPBOX_ACCESS_TOKEN = None
            mock_settings.DROPBOX_FOLDER_PATH = "/TestFolder"

            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = None
                    service.app_secret = "secret"
                    service.refresh_token = "token"

                    result = service._refresh_access_token()

                    assert result is False

    def test_refresh_fails_without_refresh_token(self):
        """Test that refresh fails when refresh_token is missing."""
        with patch('app.services.dropbox_service.settings') as mock_settings:
            mock_settings.DROPBOX_APP_KEY = "key"
            mock_settings.DROPBOX_APP_SECRET = "secret"
            mock_settings.DROPBOX_REFRESH_TOKEN = None
            mock_settings.DROPBOX_ACCESS_TOKEN = None
            mock_settings.DROPBOX_FOLDER_PATH = "/TestFolder"

            with patch('app.services.dropbox_service.Dropbox'):
                from app.services.dropbox_service import DropboxService

                with patch.object(DropboxService, '_initialize_client_with_refresh_token'):
                    service = DropboxService()
                    service.app_key = "key"
                    service.app_secret = "secret"
                    service.refresh_token = None

                    result = service._refresh_access_token()

                    assert result is False
