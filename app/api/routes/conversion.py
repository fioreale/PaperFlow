"""API routes for article conversion."""

import asyncio
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.conversion import (
    ConversionRequest,
    ConversionResponse,
    JobStatusResponse,
    JobStatus,
)
from app.services.mercury_parser import MercuryParserService
from app.services.pdf_generator import PDFGeneratorService
from app.services.dropbox_service import DropboxService
from app.services.conversion_service import ConversionService
from app.services.job_manager import job_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
mercury_service = MercuryParserService()
pdf_service = PDFGeneratorService()
dropbox_service = DropboxService()
conversion_service = ConversionService(
    mercury_service, pdf_service, dropbox_service, job_manager
)


@router.post("/convert", response_model=ConversionResponse)
async def convert_article(
    request: ConversionRequest, background_tasks: BackgroundTasks
):
    """
    Submit an article URL for conversion to PDF.

    This endpoint creates a conversion job and processes it asynchronously.
    Use the returned job_id to check the status via the /status/{job_id} endpoint.

    Args:
        request: ConversionRequest containing article URL and options

    Returns:
        ConversionResponse with job_id and initial status
    """
    try:
        # Create job
        job = job_manager.create_job(
            url=str(request.url),
            title=request.title,
            upload_to_dropbox=request.upload_to_dropbox,
        )

        # Add conversion task to background
        background_tasks.add_task(conversion_service.convert_article, job)

        logger.info(f"Created conversion job {job.job_id} for URL: {request.url}")

        return ConversionResponse(
            job_id=job.job_id,
            status=job.status,
            message="Conversion job created successfully",
            created_at=job.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to create conversion job: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create conversion job: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a conversion job.

    Args:
        job_id: Unique job identifier returned from /convert endpoint

    Returns:
        JobStatusResponse with current job status and details

    Raises:
        HTTPException: If job_id is not found
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return job.to_response()


@router.post("/convert-sync", response_model=JobStatusResponse)
async def convert_article_sync(request: ConversionRequest):
    """
    Convert an article synchronously (blocking).

    This endpoint waits for the conversion to complete before returning.
    Use this for testing or when you need immediate results.
    For production use, prefer the async /convert endpoint.

    Args:
        request: ConversionRequest containing article URL and options

    Returns:
        JobStatusResponse with completed conversion details
    """
    try:
        # Create job
        job = job_manager.create_job(
            url=str(request.url),
            title=request.title,
            upload_to_dropbox=request.upload_to_dropbox,
        )

        # Execute conversion synchronously
        await conversion_service.convert_article(job)

        # Return final status
        return job.to_response()

    except Exception as e:
        logger.error(f"Synchronous conversion failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Conversion failed: {str(e)}"
        )
