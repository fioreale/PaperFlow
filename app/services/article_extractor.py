"""Article content extraction service using trafilatura and playwright."""

import re
import trafilatura
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext
from playwright_stealth import Stealth
from app.schemas.conversion import ArticleContent


class ArticleExtractorService:
    """Service for extracting article content using trafilatura and playwright."""

    def __init__(self):
        """Initialize the article extractor service."""
        self.timeout = 60000  # 60 seconds in milliseconds for Playwright
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._stealth = Stealth()

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
        else:
            # Post-process extracted content to fix common issues
            extracted_text = self._post_process_content(extracted_text, url)

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
                # Apply stealth mode to avoid bot detection
                await self._stealth.apply_stealth_async(page)

                # Use 'load' instead of 'networkidle' for sites with continuous JS activity
                # 'load' waits for the load event (DOM + resources), which is more reliable
                # than 'networkidle' for dynamic sites like Medium
                await page.goto(
                    url,
                    wait_until='load',
                    timeout=self.timeout
                )
                # Give extra time for dynamic content to render
                await page.wait_for_timeout(2000)  # 2 seconds for JS execution
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

                    # Apply stealth mode to avoid bot detection
                    stealth_instance = Stealth()
                    await stealth_instance.apply_stealth_async(page)

                    # Use 'load' instead of 'networkidle' for sites with continuous JS activity
                    await page.goto(
                        url,
                        wait_until='load',
                        timeout=self.timeout
                    )
                    # Give extra time for dynamic content to render
                    await page.wait_for_timeout(2000)  # 2 seconds for JS execution

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

    def _post_process_content(self, html_content: str, url: str) -> str:
        """
        Post-process extracted content to fix common issues.

        Args:
            html_content: Extracted HTML content from trafilatura
            url: Source URL to determine site-specific processing

        Returns:
            Cleaned HTML content
        """
        # Apply site-specific cleaning
        if 'wikipedia.org' in url:
            html_content = self._remove_wikipedia_artifacts(html_content)

        # Apply general cleaning
        html_content = self._remove_external_link_tags(html_content)
        html_content = self._normalize_spacing(html_content)
        html_content = self._remove_empty_tags(html_content)

        return html_content

    def _remove_wikipedia_artifacts(self, html_content: str) -> str:
        """
        Remove Wikipedia-specific UI elements from extracted content.

        Args:
            html_content: HTML content extracted from Wikipedia

        Returns:
            Cleaned HTML without Wikipedia UI artifacts
        """
        # Remove [edit] section links - Pattern: [<p><a href="...action=edit...">edit</a>]</p>
        html_content = re.sub(
            r'\[<p><a\s+href="[^"]*action=edit[^"]*">edit</a>\]</p>',
            '',
            html_content
        )

        # Remove standalone [edit] links
        html_content = re.sub(
            r'\[<a\s+href="[^"]*action=edit[^"]*">edit</a>\]',
            '',
            html_content
        )

        # Remove citation needed tags [citation needed]
        html_content = re.sub(
            r'\[<a\s+href="[^"]*citation[^"]*">citation needed</a>\]',
            '',
            html_content
        )

        # Remove other Wikipedia metadata brackets like [update], [when?], etc.
        html_content = re.sub(
            r'\[<a\s+href="[^"]*">(?:update|when\?|by whom\?|clarification needed)</a>\]',
            '',
            html_content,
            flags=re.IGNORECASE
        )

        return html_content

    def _remove_external_link_tags(self, html_content: str) -> str:
        """
        Remove link tags for external references but preserve the text content.
        Keeps anchor tags that are internal page navigation (href starting with #).

        Args:
            html_content: HTML content

        Returns:
            HTML with external link tags removed but text preserved
        """
        # Remove <a> tags that link outside the page, but keep the text
        # Match <a href="...">text</a> where href doesn't start with # (internal anchor)
        def replace_external_link(match):
            href = match.group(1)
            text = match.group(2)

            # Keep internal anchor links (e.g., href="#section")
            if href.startswith('#'):
                return match.group(0)  # Return original link unchanged

            # For external links, return just the text content
            return text

        # Pattern: <a href="..." ...>text content</a>
        # Captures href value and text content between tags
        html_content = re.sub(
            r'<a\s+href="([^"]*)"[^>]*>([^<]+)</a>',
            replace_external_link,
            html_content
        )

        return html_content

    def _normalize_spacing(self, html_content: str) -> str:
        """
        Ensure proper spacing around inline elements to prevent word concatenation.

        Args:
            html_content: HTML content

        Returns:
            HTML with normalized spacing
        """
        # Add space after closing </a> tags if followed by uppercase letter
        html_content = re.sub(r'</a>([A-Z])', r'</a> \1', html_content)

        # Add space after closing </pre> tags if followed by text
        html_content = re.sub(r'</pre>([A-Za-z])', r'</pre> \1', html_content)

        # Add space after closing </code> tags if followed by text
        html_content = re.sub(r'</code>([A-Za-z])', r'</code> \1', html_content)

        # Normalize multiple spaces to single space (but preserve in <pre> tags)
        # This is a simple approach - for production, use proper HTML parsing
        html_content = re.sub(r'(?<=>)\s{2,}(?=<)', ' ', html_content)

        return html_content

    def _remove_empty_tags(self, html_content: str) -> str:
        """
        Remove empty HTML tags that don't add value.

        Args:
            html_content: HTML content

        Returns:
            HTML without empty tags
        """
        # Remove empty paragraph tags
        html_content = re.sub(r'<p>\s*</p>', '', html_content)
        html_content = re.sub(r'<p/>', '', html_content)

        # Remove empty table elements
        html_content = re.sub(r'<table>\s*</table>', '', html_content)
        html_content = re.sub(r'<table/>', '', html_content)

        # Remove multiple consecutive empty lines
        html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)

        return html_content
