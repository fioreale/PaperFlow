"""Test script for Dropbox connection and upload."""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.services.dropbox_service import DropboxService


async def test_dropbox_connection():
    """Test Dropbox connection and authentication."""
    print("=" * 80)
    print("Dropbox Connection Test")
    print("=" * 80)

    # Check if token is configured
    if not settings.DROPBOX_ACCESS_TOKEN:
        print("✗ Dropbox not configured")
        print("  DROPBOX_ACCESS_TOKEN is not set in environment")
        print(f"  Folder path configured: {settings.DROPBOX_FOLDER_PATH}")
        print("\nTo test Dropbox functionality:")
        print("  1. Get a never-expiring access token from:")
        print("     https://www.dropbox.com/developers/apps")
        print("  2. In App Console -> Settings -> Generate access token")
        print("  3. Set DROPBOX_ACCESS_TOKEN environment variable in .env file")
        print("  4. Run this test again")
        return False

    print("✓ Token is configured")
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

    if not settings.DROPBOX_ACCESS_TOKEN:
        print("⊘ Skipping - Dropbox not configured")
        return False

    try:
        service = DropboxService()
        if not service.is_configured():
            print("✗ Dropbox not configured")
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

    if not settings.DROPBOX_ACCESS_TOKEN:
        print("⊘ Skipping - Dropbox not configured")
        return False

    try:
        service = DropboxService()
        if not service.is_configured():
            print("✗ Dropbox not configured")
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


async def main():
    """Run all Dropbox tests."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 26 + "PAPERFLOW DROPBOX TEST" + " " * 30 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    results = []

    # Test 1: Connection
    result1 = await test_dropbox_connection()
    results.append(("Connection", result1))
    print()

    # Only run other tests if connection succeeded
    if result1:
        # Test 2: Folder creation
        result2 = await test_folder_creation()
        results.append(("Folder Creation", result2))
        print()

        # Test 3: File upload
        result3 = await test_file_upload()
        results.append(("File Upload", result3))
        print()

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name:<20} {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print()
    print(f"  Total: {passed}/{total} tests passed")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
