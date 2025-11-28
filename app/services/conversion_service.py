"""Main conversion service orchestrating the entire workflow."""

import logging
from typing import Optional
from app.schemas.conversion import JobStatus
from app.services.article_extractor import ArticleExtractorService
from app.services.pdf_generator import PDFGeneratorService
from app.services.dropbox_service import DropboxService
from app.services.job_manager import JobManager, Job

logger = logging.getLogger(__name__)


class ConversionService:
    """
    Main service for orchestrating article to PDF conversion.

    This service coordinates between content extraction, PDF generation,
    and cloud storage upload.
    """

    def __init__(
        self,
        extractor_service: ArticleExtractorService,
        pdf_service: PDFGeneratorService,
        dropbox_service: DropboxService,
        job_manager: JobManager,
    ):
        self.extractor = extractor_service
        self.pdf = pdf_service
        self.dropbox = dropbox_service
        self.jobs = job_manager

    async def convert_article(self, job: Job) -> None:
        """
        Execute the full conversion workflow for a job.

        Args:
            job: Job object containing conversion parameters

        This method updates the job status as it progresses through each step.
        """
        try:
            # Update status to processing
            self.jobs.update_job_status(job.job_id, JobStatus.PROCESSING)

            # Step 1: Extract article content
            logger.info(f"Extracting content for job {job.job_id} from {job.url}")
            article = await self.extractor.extract_article(job.url)

            # Update job with extracted title if not provided
            if not job.title:
                self.jobs.update_job_status(
                    job.job_id,
                    JobStatus.PROCESSING,
                    title=article.title,
                )

            # Step 2: Generate PDF
            logger.info(f"Generating PDF for job {job.job_id}")
            output_path = self.pdf.get_output_path(
                job.job_id, article.title or "article"
            )
            pdf_path = await self.pdf.generate_pdf(article, output_path)

            # Update job with PDF path
            self.jobs.update_job_status(
                job.job_id, JobStatus.PROCESSING, pdf_path=pdf_path
            )

            # Step 3: Upload to Dropbox (if configured and requested)
            dropbox_path: Optional[str] = None
            if job.upload_to_dropbox and self.dropbox.is_configured():
                logger.info(f"Uploading PDF to Dropbox for job {job.job_id}")
                try:
                    # Ensure folder exists
                    await self.dropbox.create_folder_if_not_exists()

                    # Upload file
                    dropbox_path = await self.dropbox.upload_file(pdf_path)
                    logger.info(
                        f"Successfully uploaded to Dropbox: {dropbox_path}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to upload to Dropbox for job {job.job_id}: {str(e)}"
                    )
                    # Don't fail the entire job if Dropbox upload fails
                    dropbox_path = None

            # Mark job as completed
            self.jobs.update_job_status(
                job.job_id,
                JobStatus.COMPLETED,
                pdf_path=pdf_path,
                dropbox_path=dropbox_path,
            )

            logger.info(f"Successfully completed job {job.job_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to convert article for job {job.job_id}: {error_msg}")
            self.jobs.update_job_status(
                job.job_id, JobStatus.FAILED, error=error_msg
            )
            raise
