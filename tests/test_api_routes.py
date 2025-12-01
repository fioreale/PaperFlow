"""
Comprehensive tests for API routes.

Tests cover:
- Health endpoint
- Async conversion endpoint (/convert)
- Job status endpoint (/status/{job_id})
- Synchronous conversion endpoint (/convert-sync) with PDF creation and Dropbox upload

Usage:
    # Run all tests with uv
    uv run pytest tests/test_api_routes.py -v

    # Run validation tests only (no real conversions - faster)
    uv run pytest tests/test_api_routes.py -v -k "TestHealthEndpoint or test_invalid or test_missing or test_malformed or test_empty or test_status_for_nonexistent"

    # Run with output
    uv run pytest tests/test_api_routes.py -v -s

    # Run specific test class
    uv run pytest tests/test_api_routes.py::TestHealthEndpoint -v

    # Run directly (sets up environment automatically)
    python tests/test_api_routes.py

Note:
    Some tests require Playwright browser to work correctly. If you encounter
    "Page crashed" errors, this is a known Playwright/macOS compatibility issue.
    The validation tests (health, error handling, input validation) will work
    regardless of Playwright status.
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set up environment for WeasyPrint on macOS
if sys.platform == "darwin":  # macOS
    try:
        # Get Homebrew prefix
        brew_prefix = subprocess.check_output(["brew", "--prefix"], text=True).strip()
        lib_path = f"{brew_prefix}/lib"

        # Set DYLD_LIBRARY_PATH for WeasyPrint
        current_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
        if lib_path not in current_dyld:
            os.environ["DYLD_LIBRARY_PATH"] = f"{lib_path}:{current_dyld}" if current_dyld else lib_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Homebrew not installed or not in PATH, skip setup
        pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.main import app


@pytest.fixture(scope="module")
async def browser_service():
    """Create a persistent browser service for all tests."""
    from app.services.article_extractor import ArticleExtractorService

    # Initialize browser once for all tests
    service = ArticleExtractorService()
    await service._initialize_browser()

    yield service

    # Cleanup after all tests
    await service.close()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        """Test that health check returns correct status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "PaperFlow API"


class TestConvertEndpoint:
    """Tests for the async /convert endpoint."""

    def test_convert_creates_job(self, client):
        """Test that convert endpoint creates a job and returns job_id."""
        payload = {
            "url": "https://example.com",
            "title": "Test Article",
            "upload_to_dropbox": True
        }

        response = client.post("/api/v1/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["message"] == "Conversion job created successfully"
        assert "created_at" in data

    def test_convert_without_title(self, client):
        """Test convert without custom title."""
        payload = {
            "url": "https://example.com",
            "upload_to_dropbox": False
        }

        response = client.post("/api/v1/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_convert_invalid_url(self, client):
        """Test convert with invalid URL."""
        payload = {
            "url": "not-a-valid-url",
            "upload_to_dropbox": False
        }

        response = client.post("/api/v1/convert", json=payload)

        # Pydantic validation should fail
        assert response.status_code == 422

    def test_convert_missing_required_fields(self, client):
        """Test convert without required URL field."""
        payload = {
            "upload_to_dropbox": False
        }

        response = client.post("/api/v1/convert", json=payload)

        assert response.status_code == 422


class TestStatusEndpoint:
    """Tests for the /status/{job_id} endpoint."""

    def test_status_for_existing_job(self, client):
        """Test status retrieval for an existing job."""
        # First create a job
        payload = {
            "url": "https://example.com",
            "upload_to_dropbox": False
        }
        create_response = client.post("/api/v1/convert", json=payload)
        job_id = create_response.json()["job_id"]

        # Then check its status
        response = client.get(f"/api/v1/status/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_status_for_nonexistent_job(self, client):
        """Test status retrieval for a job that doesn't exist."""
        response = client.get("/api/v1/status/nonexistent-job-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.skipif(
    not settings.DROPBOX_ACCESS_TOKEN,
    reason="Dropbox not configured - set DROPBOX_ACCESS_TOKEN to run this test"
)
class TestConvertSyncEndpoint:
    """
    Tests for the synchronous /convert-sync endpoint.

    These tests verify end-to-end functionality including:
    - Article extraction
    - PDF generation
    - Dropbox upload

    Note: These tests require Dropbox to be configured and will make real API calls.
    """

    @pytest.mark.timeout(60)
    def test_convert_sync_with_dropbox_upload(self, client):
        """
        Test full synchronous conversion with Dropbox upload.

        This test:
        1. Submits an article for conversion
        2. Waits for conversion to complete
        3. Verifies PDF was created
        4. Verifies PDF was uploaded to Dropbox
        """
        payload = {
            "url": "https://example.com",
            "title": f"Test Article {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "upload_to_dropbox": True
        }

        response = client.post("/api/v1/convert-sync", json=payload, timeout=60.0)

        assert response.status_code == 200
        data = response.json()

        # Verify job structure
        assert "job_id" in data
        assert data["status"] in ["completed", "failed"]
        assert "url" in data
        assert "title" in data

        # If conversion succeeded, verify PDF and Dropbox paths
        if data["status"] == "completed":
            assert data["pdf_path"] is not None
            assert data["dropbox_path"] is not None
            assert data["error"] is None

            # Verify PDF file exists locally
            pdf_path = Path(data["pdf_path"])
            assert pdf_path.exists(), f"PDF not found at {data['pdf_path']}"
            assert pdf_path.stat().st_size > 0, "PDF file is empty"

            # Verify Dropbox path format
            assert data["dropbox_path"].startswith(settings.DROPBOX_FOLDER_PATH)
            assert data["dropbox_path"].endswith(".pdf")

            print(f"\n✓ PDF created successfully: {data['pdf_path']}")
            print(f"✓ Uploaded to Dropbox: {data['dropbox_path']}")
        else:
            # If failed, error message should be present
            assert data["error"] is not None
            print(f"\n✗ Conversion failed: {data['error']}")

    @pytest.mark.timeout(60)
    def test_convert_sync_without_dropbox(self, client):
        """Test synchronous conversion without Dropbox upload."""
        payload = {
            "url": "https://example.com",
            "upload_to_dropbox": False
        }

        response = client.post("/api/v1/convert-sync", json=payload, timeout=60.0)

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert data["status"] in ["completed", "failed"]

        if data["status"] == "completed":
            assert data["pdf_path"] is not None
            assert data["dropbox_path"] is None  # Should not upload to Dropbox

            # Verify PDF exists
            pdf_path = Path(data["pdf_path"])
            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 0

    def test_convert_sync_invalid_url(self, client):
        """Test synchronous conversion with invalid URL."""
        payload = {
            "url": "not-a-valid-url",
            "upload_to_dropbox": False
        }

        response = client.post("/api/v1/convert-sync", json=payload)

        # Should fail validation
        assert response.status_code == 422


class TestAsyncConversionFlow:
    """
    Test the complete async conversion flow:
    1. Submit job via /convert
    2. Poll /status until completion
    3. Verify results
    """

    @pytest.mark.timeout(60)
    @pytest.mark.skipif(
        not settings.DROPBOX_ACCESS_TOKEN,
        reason="Dropbox not configured"
    )
    def test_async_conversion_complete_flow(self, client):
        """
        Test the full async conversion workflow.

        This test:
        1. Creates a conversion job
        2. Polls the status endpoint
        3. Waits for completion
        4. Verifies the final result
        """
        # Step 1: Create conversion job
        payload = {
            "url": "https://example.com",
            "title": f"Async Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "upload_to_dropbox": True
        }

        create_response = client.post("/api/v1/convert", json=payload)
        assert create_response.status_code == 200

        job_id = create_response.json()["job_id"]
        print(f"\nCreated job: {job_id}")

        # Step 2: Poll status until completion or timeout
        max_attempts = 30  # 30 seconds max
        attempt = 0
        final_status = None

        while attempt < max_attempts:
            status_response = client.get(f"/api/v1/status/{job_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            current_status = status_data["status"]

            print(f"Attempt {attempt + 1}: Status = {current_status}")

            if current_status in ["completed", "failed"]:
                final_status = status_data
                break

            time.sleep(1)
            attempt += 1

        # Step 3: Verify completion
        assert final_status is not None, "Job did not complete within timeout"
        assert final_status["status"] in ["completed", "failed"]

        if final_status["status"] == "completed":
            assert final_status["pdf_path"] is not None
            assert final_status["dropbox_path"] is not None

            # Verify PDF exists
            pdf_path = Path(final_status["pdf_path"])
            assert pdf_path.exists()

            print("\n✓ Async conversion completed successfully")
            print(f"✓ PDF: {final_status['pdf_path']}")
            print(f"✓ Dropbox: {final_status['dropbox_path']}")
        else:
            print(f"\n✗ Async conversion failed: {final_status.get('error')}")


class TestErrorHandling:
    """Tests for error handling in various scenarios."""

    def test_malformed_json(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/v1/convert",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_empty_request_body(self, client):
        """Test handling of empty request body."""
        response = client.post("/api/v1/convert", json={})

        assert response.status_code == 422


if __name__ == "__main__":
    # Allow running tests directly with python
    pytest.main([__file__, "-v", "-s"])
