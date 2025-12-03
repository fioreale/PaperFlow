"""Business logic and services."""

from app.services.article_extractor import ArticleExtractorService
from app.services.dropbox_service import DropboxService
from app.services.job_manager import JobManager, Job, job_manager

# PDFGeneratorService import is deferred to avoid WeasyPrint system dependency issues
# It will be imported when explicitly needed
try:
    from app.services.pdf_generator import PDFGeneratorService
except (ImportError, OSError):
    PDFGeneratorService = None  # type: ignore

try:
    from app.services.conversion_service import ConversionService
except (ImportError, OSError):
    ConversionService = None  # type: ignore

__all__ = [
    "ArticleExtractorService",
    "PDFGeneratorService",
    "DropboxService",
    "JobManager",
    "Job",
    "job_manager",
    "ConversionService",
]
