"""Test script for Dropbox connection and upload with refresh token support."""

import asyncio
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.services.dropbox_service import DropboxService


def _is_dropbox_configured():
    """Check if Dropbox is configured via refresh token OR legacy access token."""
    has_refresh_token = (
        settings.DROPBOX_REFRESH_TOKEN and
        settings.DROPBOX_APP_KEY and
        settings.DROPBOX_APP_SECRET
    )
    has_access_token = settings.DROPBOX_ACCESS_TOKEN
    return has_refresh_token or has_access_token


def _get_auth_method():
    """Get the authentication method being used."""
    if settings.DROPBOX_REFRESH_TOKEN and settings.DROPBOX_APP_KEY and settings.DROPBOX_APP_SECRET:
        return "refresh_token"
    elif settings.DROPBOX_ACCESS_TOKEN:
        return "access_token"
    return None


async def test_dropbox_connection():
    """Test Dropbox connection and authentication."""
    print("=" * 80)
    print("Dropbox Connection Test")
    print("=" * 80)

    # Check if Dropbox is configured (refresh token or access token)
    if not _is_dropbox_configured():
        print("✗ Dropbox not configured")
        print("  Neither refresh token nor access token is set")
        print(f"  Folder path configured: {settings.DROPBOX_FOLDER_PATH}")
        print("\nTo configure Dropbox (recommended - OAuth 2.0 with refresh token):")
        print("  1. Create app at https://www.dropbox.com/developers/apps")
        print("  2. Run: python scripts/get_dropbox_refresh_token.py")
        print("  3. Set DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN in .env")
        print("\nAlternative (legacy - access token):")
        print("  Set DROPBOX_ACCESS_TOKEN in .env file")
        return False

    auth_method = _get_auth_method()
    print(f"✓ Dropbox configured via {auth_method}")
    print(f"  Folder path: {settings.DROPBOX_FOLDER_PATH}")
    print()

    try:
        service = DropboxService()
        is_configured = service.is_configured()

        if is_configured:
            print("✓ Dropbox client initialized successfully!")

            # Get account info
            try:
                account = service.client.users_get_current_account()
                print(f"✓ Connected to account: {account.name.display_name}")
                print(f"  Email: {account.email}")
                print()
            except Exception as e:
                print(f"⚠ Could not retrieve account info: {str(e)}")
                print()

            return True
        else:
            print("✗ Dropbox client failed to initialize")
            return False

    except Exception as e:
        print("✗ Dropbox initialization failed!")
        print(f"  Error: {type(e).__name__}: {str(e)}")
        return False


async def test_folder_creation():
    """Test folder creation in Dropbox."""
    print("=" * 80)
    print("Folder Creation Test")
    print("=" * 80)

    if not _is_dropbox_configured():
        print("⊘ Skipping - Dropbox not configured")
        return False

    try:
        service = DropboxService()
        if not service.is_configured():
            print("✗ Dropbox client failed to initialize")
            return False

        print(f"Testing folder: {settings.DROPBOX_FOLDER_PATH}")
        await service.create_folder_if_not_exists()
        print("✓ Folder exists or was created successfully!")
        return True

    except Exception as e:
        print("✗ Folder creation failed!")
        print(f"  Error: {type(e).__name__}: {str(e)}")
        return False


async def test_file_upload():
    """Test file upload to Dropbox."""
    print("=" * 80)
    print("File Upload Test")
    print("=" * 80)

    if not _is_dropbox_configured():
        print("⊘ Skipping - Dropbox not configured")
        return False

    try:
        service = DropboxService()
        if not service.is_configured():
            print("✗ Dropbox client failed to initialize")
            return False

        # Create a test file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_content = f"PaperFlow Dropbox Test\nTimestamp: {timestamp}\n"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            test_filename = f"test_{timestamp}.txt"
            print(f"Uploading test file: {test_filename}")
            print(f"  Local path: {temp_path}")

            dropbox_path = await service.upload_file(temp_path, test_filename)
            print("✓ File uploaded successfully!")
            print(f"  Dropbox path: {dropbox_path}")

            return True

        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        print("✗ File upload failed!")
        print(f"  Error: {type(e).__name__}: {str(e)}")
        return False


async def test_refresh_token_mechanism():
    """Test the refresh token mechanism explicitly."""
    print("=" * 80)
    print("Refresh Token Mechanism Test")
    print("=" * 80)

    # This test only applies to refresh token auth
    if _get_auth_method() != "refresh_token":
        print("⊘ Skipping - Not using refresh token authentication")
        return None  # None indicates skipped, not failed

    try:
        # Create a fresh service instance
        service = DropboxService()

        if not service.is_configured():
            print("✗ Service failed to initialize")
            return False

        # Verify refresh token credentials are set
        print(f"✓ App Key: {service.app_key[:8]}...")
        print(f"✓ App Secret: {service.app_secret[:4]}...")
        print(f"✓ Refresh Token: {service.refresh_token[:20]}...")

        # Check that access token was obtained during initialization
        if service.access_token:
            print(f"✓ Access Token obtained: {service.access_token[:20]}...")
        else:
            print("✗ No access token obtained")
            return False

        # Check token expiration is set
        if service.token_expires_at:
            now = datetime.now(timezone.utc)
            time_until_expiry = service.token_expires_at - now
            print(f"✓ Token expires at: {service.token_expires_at.isoformat()}")
            print(f"  Time until expiry: {time_until_expiry}")

            # Verify expiration is in the future (should be ~4 hours minus 5 min buffer)
            if time_until_expiry.total_seconds() > 0:
                print("✓ Token expiration is in the future")
            else:
                print("✗ Token already expired!")
                return False
        else:
            print("✗ Token expiration not set")
            return False

        # Test manual refresh
        print("\nTesting manual token refresh...")
        old_token = service.access_token
        old_expiry = service.token_expires_at

        result = service._refresh_access_token()
        if result:
            print("✓ Manual refresh successful")
            if service.access_token != old_token:
                print("✓ New access token obtained")
            if service.token_expires_at != old_expiry:
                print("✓ New expiration time set")
        else:
            print("✗ Manual refresh failed")
            return False

        return True

    except Exception as e:
        print(f"✗ Test failed with error: {type(e).__name__}: {str(e)}")
        return False


async def test_token_expiration_handling():
    """Test automatic token renewal when token is expired."""
    print("=" * 80)
    print("Token Expiration Handling Test")
    print("=" * 80)

    if _get_auth_method() != "refresh_token":
        print("⊘ Skipping - Not using refresh token authentication")
        return None

    try:
        service = DropboxService()

        if not service.is_configured():
            print("✗ Service failed to initialize")
            return False

        # Save original values
        original_token = service.access_token
        original_expiry = service.token_expires_at
        print(f"✓ Initial token: {original_token[:20]}...")
        print(f"  Initial expiry: {original_expiry}")

        # Simulate expired token by setting expiration to the past
        print("\nSimulating expired token...")
        service.token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        print(f"  Set expiry to: {service.token_expires_at} (past)")

        # Call _ensure_valid_token - should trigger refresh
        print("\nCalling _ensure_valid_token()...")
        result = service._ensure_valid_token()

        if result:
            print("✓ _ensure_valid_token() returned True")

            # Verify token was refreshed
            if service.token_expires_at > datetime.now(timezone.utc):
                print("✓ Token expiration is now in the future")
                print(f"  New expiry: {service.token_expires_at}")
            else:
                print("✗ Token still appears expired")
                return False

            # Verify we can still make API calls
            print("\nVerifying API access with refreshed token...")
            account = service.client.users_get_current_account()
            print(f"✓ API call successful - Account: {account.name.display_name}")

            return True
        else:
            print("✗ _ensure_valid_token() returned False")
            return False

    except Exception as e:
        print(f"✗ Test failed with error: {type(e).__name__}: {str(e)}")
        return False


async def test_token_info_display():
    """Display current token information for debugging."""
    print("=" * 80)
    print("Token Information")
    print("=" * 80)

    auth_method = _get_auth_method()
    print(f"Authentication method: {auth_method or 'None'}")
    print()

    if auth_method == "refresh_token":
        print("OAuth 2.0 Credentials:")
        print(f"  DROPBOX_APP_KEY: {settings.DROPBOX_APP_KEY[:8]}..." if settings.DROPBOX_APP_KEY else "  DROPBOX_APP_KEY: Not set")
        print(f"  DROPBOX_APP_SECRET: {'*' * 8}" if settings.DROPBOX_APP_SECRET else "  DROPBOX_APP_SECRET: Not set")
        print(f"  DROPBOX_REFRESH_TOKEN: {settings.DROPBOX_REFRESH_TOKEN[:20]}..." if settings.DROPBOX_REFRESH_TOKEN else "  DROPBOX_REFRESH_TOKEN: Not set")
    elif auth_method == "access_token":
        print("Legacy Access Token:")
        print(f"  DROPBOX_ACCESS_TOKEN: {settings.DROPBOX_ACCESS_TOKEN[:20]}..." if settings.DROPBOX_ACCESS_TOKEN else "  Not set")

    print(f"\nDROPBOX_FOLDER_PATH: {settings.DROPBOX_FOLDER_PATH}")

    if auth_method:
        try:
            service = DropboxService()
            if service.is_configured():
                print("\nService Status:")
                print(f"  Client initialized: Yes")
                if service.token_expires_at:
                    now = datetime.now(timezone.utc)
                    remaining = service.token_expires_at - now
                    print(f"  Token expires at: {service.token_expires_at.isoformat()}")
                    print(f"  Time remaining: {remaining}")
                else:
                    print("  Token expiration: Not tracked (legacy token)")

                # Test API access
                account = service.client.users_get_current_account()
                print(f"  Account: {account.name.display_name} ({account.email})")
        except Exception as e:
            print(f"\n  Error: {str(e)}")

    return True


async def main():
    """Run all Dropbox tests."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 26 + "PAPERFLOW DROPBOX TEST" + " " * 30 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    results = []

    # Test 0: Token Info (always runs)
    await test_token_info_display()
    print()

    # Test 1: Connection
    result1 = await test_dropbox_connection()
    results.append(("Connection", result1))
    print()

    # Only run other tests if connection succeeded
    if result1:
        # Test 2: Refresh Token Mechanism (if using refresh token auth)
        result_refresh = await test_refresh_token_mechanism()
        if result_refresh is not None:  # None means skipped
            results.append(("Refresh Token", result_refresh))
            print()

        # Test 3: Token Expiration Handling (if using refresh token auth)
        result_expiry = await test_token_expiration_handling()
        if result_expiry is not None:
            results.append(("Token Expiration", result_expiry))
            print()

        # Test 4: Folder creation
        result2 = await test_folder_creation()
        results.append(("Folder Creation", result2))
        print()

        # Test 5: File upload
        result3 = await test_file_upload()
        results.append(("File Upload", result3))
        print()

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name:<25} {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print()
    print(f"  Total: {passed}/{total} tests passed")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
