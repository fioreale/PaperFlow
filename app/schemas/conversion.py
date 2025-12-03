"""Schemas for article conversion."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field, ConfigDict


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversionRequest(BaseModel):
    """Request schema for article conversion."""

    url: HttpUrl = Field(..., description="URL of the article to convert")
    title: Optional[str] = Field(None, description="Optional custom title for the PDF")
    upload_to_dropbox: bool = Field(
        True, description="Whether to upload the PDF to Dropbox"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com/article",
                "title": "My Custom Title",
                "upload_to_dropbox": True,
            }
        }
    )


class ConversionResponse(BaseModel):
    """Response schema for conversion request."""

    job_id: str = Field(..., description="Unique identifier for the conversion job")
    status: JobStatus = Field(..., description="Current status of the job")
    message: str = Field(..., description="Human-readable message about the job")
    created_at: datetime = Field(..., description="Timestamp when the job was created")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "abc123",
                "status": "pending",
                "message": "Conversion job created successfully",
                "created_at": "2025-01-15T10:30:00Z",
            }
        }
    )


class JobStatusResponse(BaseModel):
    """Response schema for job status query."""

    job_id: str = Field(..., description="Unique identifier for the conversion job")
    status: JobStatus = Field(..., description="Current status of the job")
    url: Optional[str] = Field(None, description="Original article URL")
    title: Optional[str] = Field(None, description="Article title")
    pdf_path: Optional[str] = Field(None, description="Local path to generated PDF")
    dropbox_path: Optional[str] = Field(None, description="Dropbox path if uploaded")
    error: Optional[str] = Field(None, description="Error message if job failed")
    created_at: datetime = Field(..., description="Timestamp when job was created")
    updated_at: datetime = Field(..., description="Timestamp of last update")
    completed_at: Optional[datetime] = Field(
        None, description="Timestamp when job completed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "abc123",
                "status": "completed",
                "url": "https://example.com/article",
                "title": "Example Article",
                "pdf_path": "/tmp/paperflow/abc123.pdf",
                "dropbox_path": "/PaperFlow/Example_Article.pdf",
                "error": None,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:45Z",
                "completed_at": "2025-01-15T10:30:45Z",
            }
        }
    )


class ArticleContent(BaseModel):
    """Schema for extracted article content."""

    title: str
    author: Optional[str] = None
    content: str
    excerpt: Optional[str] = None
    lead_image_url: Optional[str] = None
    date_published: Optional[str] = None
    url: str
