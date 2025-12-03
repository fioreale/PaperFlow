"""PDF generation service using Playwright (memory-optimized)."""

import os
import gc
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings
from app.schemas.conversion import ArticleContent


class PDFGeneratorService:
    """Service for generating PDFs from article content using Playwright.

    This implementation uses Playwright's headless Chromium to render HTML to PDF.
    It's more memory-efficient than WeasyPrint for constrained environments (256MB RAM).
    """

    def __init__(self):
        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template_dir = template_dir

        # Ensure temp directory exists
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    async def generate_pdf(
        self, article: ArticleContent, output_path: str
    ) -> str:
        """
        Generate a PDF from article content using Playwright.

        Args:
            article: ArticleContent object with extracted data
            output_path: Path where the PDF should be saved

        Returns:
            Path to the generated PDF file

        Raises:
            Exception: If PDF generation fails
        """
        html_file = None
        try:
            # Load CSS
            css_path = self.template_dir / "eink_styles.css"
            with open(css_path, "r") as f:
                css_content = f.read()

            # Truncate content if too large (memory protection)
            content = article.content
            max_length = getattr(settings, 'MAX_ARTICLE_LENGTH', 500_000)
            if len(content) > max_length:
                content = content[:max_length]
                content += "\n\n<p><em>[Content truncated due to length]</em></p>"

            # Prepare template data
            template_data = {
                "title": article.title,
                "author": article.author,
                "date_published": article.date_published,
                "url": article.url,
                "content": content,
                "css": css_content,
            }

            # Render HTML from template
            template = self.env.get_template("article.html")
            html_content = template.render(**template_data)

            # Write HTML to temporary file
            html_file = f"{output_path}.temp.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Clear large variables from memory
            del html_content, css_content, template_data, content
            gc.collect()

            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Generate PDF using Playwright with memory-optimized settings
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        # Memory optimizations
                        '--disable-dev-shm-usage',  # Use /tmp instead of /dev/shm
                        '--disable-gpu',
                        '--disable-software-rasterizer',
                        '--no-sandbox',
                        '--single-process',  # Use single process to save memory
                        '--disable-background-networking',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-breakpad',
                        '--disable-component-extensions-with-background-pages',
                        '--disable-extensions',
                        '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                        '--disable-ipc-flooding-protection',
                        '--disable-renderer-backgrounding',
                        '--enable-features=NetworkService,NetworkServiceInProcess',
                        '--force-color-profile=srgb',
                        '--hide-scrollbars',
                        '--metrics-recording-only',
                        '--mute-audio',
                        '--no-first-run',
                        # Memory limits
                        '--js-flags=--max-old-space-size=128',  # Limit V8 heap to 128MB
                    ]
                )

                try:
                    page = await browser.new_page()

                    # Navigate to the HTML file
                    await page.goto(f"file://{os.path.abspath(html_file)}", wait_until="networkidle")

                    # Generate PDF with settings matching your requirements
                    await page.pdf(
                        path=output_path,
                        format=settings.PDF_PAGE_SIZE,
                        margin={
                            'top': settings.PDF_MARGIN,
                            'right': settings.PDF_MARGIN,
                            'bottom': settings.PDF_MARGIN,
                            'left': settings.PDF_MARGIN,
                        },
                        print_background=False,  # Don't print background colors (e-ink optimization)
                        prefer_css_page_size=False,
                    )

                finally:
                    await browser.close()

            # Cleanup temporary HTML file
            if html_file and os.path.exists(html_file):
                os.unlink(html_file)
                html_file = None

            # Force garbage collection
            gc.collect()

            return output_path

        except Exception as e:
            # Cleanup on error
            if html_file and os.path.exists(html_file):
                os.unlink(html_file)
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
