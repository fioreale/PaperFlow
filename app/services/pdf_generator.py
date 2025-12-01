"""PDF generation service using WeasyPrint."""

import os
from pathlib import Path
from typing import Optional
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings
from app.schemas.conversion import ArticleContent


class PDFGeneratorService:
    """Service for generating PDFs from article content using WeasyPrint."""

    def __init__(self):
        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Load CSS template
        css_path = template_dir / "eink_styles.css"
        with open(css_path, "r") as f:
            self.css_content = f.read()

        # Ensure temp directory exists
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    async def generate_pdf(
        self, article: ArticleContent, output_path: str
    ) -> str:
        """
        Generate a PDF from article content.

        Args:
            article: ArticleContent object with extracted data
            output_path: Path where the PDF should be saved

        Returns:
            Path to the generated PDF file

        Raises:
            Exception: If PDF generation fails
        """
        try:
            # Prepare template data
            template_data = {
                "title": article.title,
                "author": article.author,
                "date_published": article.date_published,
                "url": article.url,
                "content": article.content,
                "css": self.css_content,
            }

            # Render HTML from template
            template = self.env.get_template("article.html")
            html_content = template.render(**template_data)

            # Generate PDF using WeasyPrint
            html = HTML(string=html_content)
            css = CSS(string=self.css_content)

            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write PDF to file
            html.write_pdf(output_path, stylesheets=[css])

            return output_path

        except Exception as e:
            raise Exception(f"Failed to generate PDF: {str(e)}")

    def sanitize_filename(self, title: str) -> str:
        """
        Sanitize article title for use as filename.

        Args:
            title: Article title

        Returns:
            Sanitized filename
        """
        # Remove invalid characters (including control characters)
        invalid_chars = '<>:"/\\|?*\n\t\r'
        filename = title
        for char in invalid_chars:
            filename = filename.replace(char, "_")

        # Limit length
        max_length = 100
        if len(filename) > max_length:
            filename = filename[:max_length]

        # Remove leading/trailing spaces and dots
        filename = filename.strip(". ")

        # Ensure filename is not empty
        if not filename:
            filename = "article"

        return f"{filename}.pdf"

    def get_output_path(self, job_id: str, title: str) -> str:
        """
        Generate output path for PDF file.

        Args:
            job_id: Unique job identifier
            title: Article title

        Returns:
            Full path to output PDF file
        """
        filename = self.sanitize_filename(title)
        return os.path.join(settings.TEMP_DIR, filename)
