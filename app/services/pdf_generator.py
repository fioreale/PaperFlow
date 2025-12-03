"""PDF generation service using Playwright (memory-optimized)."""

import os
import gc
import logging
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings
from app.schemas.conversion import ArticleContent

logger = logging.getLogger(__name__)


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
            browser = None
            page = None

            try:
                logger.info("Starting Playwright for PDF generation")
                async with async_playwright() as p:
                    # Launch browser with timeout
                    logger.info("Launching Chromium browser...")
                    browser = await p.chromium.launch(
                        headless=True,
                        timeout=60000,  # 60 second timeout for browser launch in low memory
                        args=[
                            # Memory optimizations
                            '--disable-dev-shm-usage',  # Use /tmp instead of /dev/shm
                            '--disable-gpu',
                            '--disable-software-rasterizer',
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
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
                            '--disable-sync',
                            '--disable-translate',
                            '--disable-default-apps',
                            # Memory limits
                            '--js-flags=--max-old-space-size=96',  # Limit V8 heap to 96MB
                        ]
                    )

                    # Validate browser is connected before proceeding
                    if not browser or not browser.is_connected():
                        logger.error("Browser failed to launch or connect")
                        raise Exception("Browser failed to launch or connect")

                    logger.info(f"Browser launched successfully (connected: {browser.is_connected()})")

                    # Small delay to ensure browser is fully initialized
                    await asyncio.sleep(0.5)

                    # Create new page with error handling
                    try:
                        logger.info("Creating new browser page...")
                        page = await browser.new_page()
                        logger.info("Browser page created successfully")
                    except Exception as e:
                        logger.error(f"Failed to create new page: {str(e)}")
                        raise Exception(f"Failed to create new page: {str(e)}")

                    # Navigate to the HTML file with timeout
                    try:
                        logger.info(f"Loading HTML file: {html_file}")
                        await page.goto(
                            f"file://{os.path.abspath(html_file)}",
                            wait_until="networkidle",
                            timeout=30000  # 30 second timeout
                        )
                        logger.info("HTML file loaded successfully")
                    except Exception as e:
                        logger.error(f"Failed to load HTML file: {str(e)}")
                        raise Exception(f"Failed to load HTML file: {str(e)}")

                    # Generate PDF with settings matching your requirements
                    try:
                        logger.info(f"Generating PDF to: {output_path}")
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
                        logger.info("PDF generated successfully")
                    except Exception as e:
                        logger.error(f"Failed to generate PDF: {str(e)}")
                        raise Exception(f"Failed to generate PDF: {str(e)}")

                    # Cleanup page before browser
                    if page:
                        logger.info("Closing browser page...")
                        await page.close()
                        page = None

                    if browser:
                        logger.info("Closing browser...")
                        await browser.close()
                        browser = None

            except Exception as e:
                logger.error(f"PDF generation error: {str(e)}")
                # Ensure cleanup on error
                if page:
                    try:
                        logger.info("Cleaning up page after error...")
                        await page.close()
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to close page during cleanup: {cleanup_error}")
                if browser:
                    try:
                        logger.info("Cleaning up browser after error...")
                        await browser.close()
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to close browser during cleanup: {cleanup_error}")
                raise

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

    def get_output_path(self, _job_id: str, title: str) -> str:
        """
        Generate output path for PDF file.

        Args:
            _job_id: Unique job identifier (currently unused)
            title: Article title

        Returns:
            Full path to output PDF file
        """
        filename = self.sanitize_filename(title)
        return os.path.join(settings.TEMP_DIR, filename)
