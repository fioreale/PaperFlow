"""Test script for Dropbox connection and upload."""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.dropbox_service import DropboxService
from app.core.config import settings


async def test_dropbox_connection():
    """Test Dropbox connection and authentication."""
    print("=" * 80)
    print("Dropbox Connection Test")
    print("=" * 80)

    # Check if token is configured
    if not settings.DROPBOX_ACCESS_TOKEN:
        print("✗ Dropbox not configured")
        print(f"  DROPBOX_ACCESS_TOKEN is not set in environment")
        print(f"  Folder path configured: {settings.DROPBOX_FOLDER_PATH}")
        print("\nTo test Dropbox functionality:")
        print("  1. Set DROPBOX_ACCESS_TOKEN environment variable")
        print("  2. Run this test again")
        return False

    print(f"✓ Token is configured")
    print(f"  Folder path: {settings.DROPBOX_FOLDER_PATH}")
    print()

    try:
        service = DropboxService()
        is_configured = service.is_configured()

        if is_configured:
            print("✓ Dropbox client initialized successfully!")
            return True
        else:
            print("✗ Dropbox client failed to initialize")
            return False

    except Exception as e:
        print(f"✗ Dropbox initialization failed!")
        print(f"  Error: {type(e).__name__}: {str(e)}")
        return False


async def main():
    """Run Dropbox connection test."""
    print()
    await test_dropbox_connection()
    print("\n" + "=" * 80)
    print("Dropbox Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
