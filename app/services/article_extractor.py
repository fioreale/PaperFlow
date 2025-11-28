"""Article content extraction service using trafilatura and playwright."""

import trafilatura
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext
from app.schemas.conversion import ArticleContent


class ArticleExtractorService:
    """Service for extracting article content using trafilatura and playwright."""

    def __init__(self):
        """Initialize the article extractor service."""
        self.timeout = 30000  # 30 seconds in milliseconds for Playwright
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self):
        """Async context manager entry - initialize browser."""
        await self._initialize_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup browser."""
        await self.close()

    async def _initialize_browser(self):
        """Initialize a persistent browser instance for reuse."""
        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self._context = await self._browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=False,
            )

    async def close(self):
        """Close the browser and cleanup resources."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def extract_article(self, url: str) -> ArticleContent:
        """
        Extract article content from a URL using trafilatura.

        Args:
            url: The URL of the article to extract

        Returns:
            ArticleContent object with extracted data

        Raises:
            Exception: If extraction fails
        """
        # Fetch the HTML content
        html_content = await self._fetch_html(url)

        # Extract content using trafilatura
        extracted_text = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=True,
            include_images=True,
            include_links=True,
            output_format="html",
            favor_precision=False,  # Favor recall to get more content
            favor_recall=True,
        )

        # Extract metadata
        metadata = trafilatura.extract_metadata(html_content)

        # Build the ArticleContent object
        title = self._get_title(metadata, html_content)
        author = self._get_author(metadata)
        date_published = self._get_date(metadata)
        excerpt = self._get_excerpt(metadata)

        # If extraction failed, fall back to basic extraction
        if not extracted_text:
            extracted_text = html_content

        return ArticleContent(
            title=title,
            author=author,
            content=extracted_text,
            excerpt=excerpt,
            lead_image_url=None,  # trafilatura doesn't extract lead image URL directly
            date_published=date_published,
            url=url,
        )

    async def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from a URL using Playwright for JavaScript rendering.

        Args:
            url: The URL to fetch

        Returns:
            HTML content as a string

        Raises:
            Exception: If fetching fails
        """
        # Use persistent browser if available, otherwise create temporary one
        if self._context:
            page = await self._context.new_page()
            try:
                await page.goto(
                    url,
                    wait_until='networkidle',
                    timeout=self.timeout
                )
                html_content = await page.content()
                return html_content
            finally:
                await page.close()
        else:
            # Fallback to one-off browser instance
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                try:
                    context = await browser.new_context(
                        user_agent=self.user_agent,
                        viewport={'width': 1920, 'height': 1080},
                        ignore_https_errors=False,
                    )

                    page = await context.new_page()

                    await page.goto(
                        url,
                        wait_until='networkidle',
                        timeout=self.timeout
                    )

                    html_content = await page.content()
                    return html_content

                finally:
                    await browser.close()

    def _get_title(self, metadata, html_content: str) -> str:
        """Extract title from metadata or HTML."""
        if metadata and metadata.title:
            return metadata.title

        # Fallback to basic HTML parsing
        import re
        title_match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()

        return "Untitled Article"

    def _get_author(self, metadata) -> Optional[str]:
        """Extract author from metadata."""
        if metadata and metadata.author:
            return metadata.author
        return None

    def _get_date(self, metadata) -> Optional[str]:
        """Extract publication date from metadata."""
        if metadata and metadata.date:
            return metadata.date
        return None

    def _get_excerpt(self, metadata) -> Optional[str]:
        """Extract excerpt/description from metadata."""
        if metadata and metadata.description:
            return metadata.description
        return None
