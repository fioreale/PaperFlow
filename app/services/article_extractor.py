"""Article content extraction service using trafilatura."""

import httpx
import trafilatura
from typing import Optional
from app.schemas.conversion import ArticleContent


class ArticleExtractorService:
    """Service for extracting article content using trafilatura."""

    def __init__(self):
        """Initialize the article extractor service."""
        self.timeout = 30.0
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

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
        Fetch HTML content from a URL.

        Args:
            url: The URL to fetch

        Returns:
            HTML content as a string

        Raises:
            Exception: If fetching fails
        """
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": self.user_agent},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

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
