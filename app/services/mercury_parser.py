"""Mercury Parser service for article content extraction."""

import httpx
from typing import Optional
from app.core.config import settings
from app.schemas.conversion import ArticleContent


class MercuryParserService:
    """Service for extracting article content using Mercury Parser API."""

    def __init__(self):
        self.api_url = settings.MERCURY_API_URL
        self.api_key = settings.MERCURY_API_KEY

    async def extract_article(self, url: str) -> ArticleContent:
        """
        Extract article content from a URL.

        Args:
            url: The URL of the article to extract

        Returns:
            ArticleContent object with extracted data

        Raises:
            Exception: If extraction fails
        """
        if self.api_key:
            # Use Mercury Parser API if key is available
            return await self._extract_with_api(url)
        else:
            # Fallback to basic extraction
            return await self._extract_basic(url)

    async def _extract_with_api(self, url: str) -> ArticleContent:
        """Extract content using Mercury Parser API."""
        headers = {"x-api-key": self.api_key}
        params = {"url": url}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.api_url, headers=headers, params=params
            )
            response.raise_for_status()
            data = response.json()

            return ArticleContent(
                title=data.get("title", "Untitled"),
                author=data.get("author"),
                content=data.get("content", ""),
                excerpt=data.get("excerpt"),
                lead_image_url=data.get("lead_image_url"),
                date_published=data.get("date_published"),
                url=url,
            )

    async def _extract_basic(self, url: str) -> ArticleContent:
        """
        Fallback basic extraction when Mercury API is not available.

        This is a simple implementation that fetches the page content.
        For production use, consider integrating a library like newspaper3k
        or readability-lxml for better content extraction.
        """
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

            # Basic extraction - in production, use a proper parser
            # For now, we'll use the raw HTML and let WeasyPrint handle it
            # This is a simplified approach
            title = self._extract_title(html_content)

            return ArticleContent(
                title=title,
                author=None,
                content=html_content,  # Full HTML for WeasyPrint
                excerpt=None,
                lead_image_url=None,
                date_published=None,
                url=url,
            )

    def _extract_title(self, html: str) -> str:
        """Extract title from HTML using basic parsing."""
        # Simple title extraction
        import re

        title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        return "Untitled Article"
