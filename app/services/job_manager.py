"""Job management service for tracking conversion jobs."""

import uuid
from datetime import datetime
from typing import Dict, Optional
from app.schemas.conversion import JobStatus, JobStatusResponse


class Job:
    """Represents a conversion job."""

    def __init__(
        self,
        job_id: str,
        url: str,
        title: Optional[str] = None,
        upload_to_dropbox: bool = True,
    ):
        self.job_id = job_id
        self.url = url
        self.title = title
        self.upload_to_dropbox = upload_to_dropbox
        self.status = JobStatus.PENDING
        self.pdf_path: Optional[str] = None
        self.dropbox_path: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

    def update_status(self, status: JobStatus, error: Optional[str] = None):
        """Update job status."""
        self.status = status
        self.updated_at = datetime.utcnow()
        if error:
            self.error = error
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            self.completed_at = datetime.utcnow()

    def to_response(self) -> JobStatusResponse:
        """Convert job to API response."""
        return JobStatusResponse(
            job_id=self.job_id,
            status=self.status,
            url=self.url,
            title=self.title,
            pdf_path=self.pdf_path,
            dropbox_path=self.dropbox_path,
            error=self.error,
            created_at=self.created_at,
            updated_at=self.updated_at,
            completed_at=self.completed_at,
        )


class JobManager:
    """
    In-memory job manager for tracking conversion jobs.

    For production use with multiple workers, consider using Redis
    or a database for persistent storage.
    """

    def __init__(self):
        self._jobs: Dict[str, Job] = {}

    def create_job(
        self, url: str, title: Optional[str] = None, upload_to_dropbox: bool = True
    ) -> Job:
        """
        Create a new conversion job.

        Args:
            url: Article URL
            title: Optional custom title
            upload_to_dropbox: Whether to upload to Dropbox

        Returns:
            Created Job object
        """
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id, url=url, title=title, upload_to_dropbox=upload_to_dropbox
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job object or None if not found
        """
        return self._jobs.get(job_id)

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
        pdf_path: Optional[str] = None,
        dropbox_path: Optional[str] = None,
        title: Optional[str] = None,
    ):
        """
        Update job status and metadata.

        Args:
            job_id: Job identifier
            status: New job status
            error: Error message if failed
            pdf_path: Path to generated PDF
            dropbox_path: Dropbox path if uploaded
            title: Article title if extracted
        """
        job = self._jobs.get(job_id)
        if job:
            job.update_status(status, error)
            if pdf_path:
                job.pdf_path = pdf_path
            if dropbox_path:
                job.dropbox_path = dropbox_path
            if title:
                job.title = title

    def delete_job(self, job_id: str):
        """
        Delete a job.

        Args:
            job_id: Job identifier
        """
        if job_id in self._jobs:
            del self._jobs[job_id]

    def get_all_jobs(self) -> Dict[str, Job]:
        """Get all jobs (for debugging/admin purposes)."""
        return self._jobs.copy()

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Clean up jobs older than specified hours.

        Args:
            max_age_hours: Maximum age in hours
        """
        now = datetime.utcnow()
        jobs_to_delete = []

        for job_id, job in self._jobs.items():
            age_hours = (now - job.created_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                jobs_to_delete.append(job_id)

        for job_id in jobs_to_delete:
            del self._jobs[job_id]


# Global job manager instance
job_manager = JobManager()
