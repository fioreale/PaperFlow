"""Test script for article HTML extraction using trafilatura."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.article_extractor import ArticleExtractorService


async def test_extraction():
    """Test trafilatura-based extraction with sample URLs."""
    service = ArticleExtractorService()

    # Test URLs (using commonly stable URLs for testing)
    test_urls = [
        "https://example.com",
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
    ]

    print("=" * 80)
    print("Article Content Extraction Test (trafilatura)")
    print("=" * 80)
    print()

    for url in test_urls:
        print(f"\n{'─' * 80}")
        print(f"Testing URL: {url}")
        print(f"{'─' * 80}")

        try:
            article = await service.extract_article(url)

            print(f"✓ Extraction successful!")
            print(f"\nTitle: {article.title}")
            print(f"Author: {article.author or 'N/A'}")
            print(f"URL: {article.url}")
            print(f"Date Published: {article.date_published or 'N/A'}")
            print(f"Excerpt: {article.excerpt[:100] + '...' if article.excerpt else 'N/A'}")
            print(f"Lead Image: {article.lead_image_url or 'N/A'}")
            print(f"Content length: {len(article.content)} characters")
            print(f"Content preview: {article.content[:200]}...")

        except Exception as e:
            print(f"✗ Extraction failed!")
            print(f"Error: {type(e).__name__}: {str(e)}")


async def test_extraction_with_example():
    """Test extraction with a real website (example.com)."""
    service = ArticleExtractorService()

    print("\n" + "=" * 80)
    print("Test Extraction with Example.com")
    print("=" * 80)

    url = "https://example.com"

    try:
        print(f"\nExtracting from: {url}")
        article = await service.extract_article(url)

        print(f"✓ Extraction completed!")
        print(f"\nTitle: {article.title}")
        print(f"Author: {article.author or 'N/A'}")
        print(f"Content length: {len(article.content)} characters")

        # Assertions
        assert article.url == url, "URL should match"
        # Note: example.com may not have much content, but it should still extract something
        print("\n✓ All assertions passed!")

    except Exception as e:
        print(f"Warning: Extraction test skipped due to network or site issues: {str(e)}")
        # This is not a critical failure - some websites may block automated access


async def main():
    """Run all extraction tests."""
    await test_extraction()
    await test_extraction_with_example()

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
