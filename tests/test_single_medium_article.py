"""Test scraping a specific Medium article.

This test will fetch and analyze the SMTP mail server article from Medium.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.article_extractor import ArticleExtractorService

# Create output directory for test results
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "medium_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def test_medium_article():
    """Test scraping a specific Medium article."""

    url = "https://medium.com/code-develop-engineer/build-an-smtp-mail-server-with-express-node-and-gmail-7e58ee84de52"

    print("=" * 80)
    print("Medium Article Scraping Test")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async with ArticleExtractorService() as service:
        try:
            print("[STEP 1] Fetching HTML with Playwright...")
            raw_html = await service._fetch_html(url)
            html_size = len(raw_html)
            print(f"  ✓ Successfully fetched {html_size:,} characters")

            # Save raw HTML
            raw_file = OUTPUT_DIR / f"{timestamp}_raw.html"
            raw_file.write_text(raw_html, encoding="utf-8")
            print(f"  ✓ Saved raw HTML to: {raw_file}")

            print("\n[STEP 2] Analyzing HTML content...")
            has_react = "react" in raw_html.lower()
            script_count = raw_html.count("<script")
            div_count = raw_html.count("<div")
            p_count = raw_html.count("<p")
            a_count = raw_html.count("<a")

            print(f"  - React detected: {has_react}")
            print(f"  - Script tags: {script_count}")
            print(f"  - Div tags: {div_count}")
            print(f"  - Paragraph tags: {p_count}")
            print(f"  - Link tags: {a_count}")

            print("\n[STEP 3] Extracting article content...")
            result = await service.extract_article(url)

            print(f"  ✓ Article extracted successfully!")
            print(f"  - Title: {result.title}")
            print(f"  - Author: {result.author}")
            print(f"  - Published: {result.date_published}")

            # Calculate word count and reading time
            word_count = len(result.content.split())
            reading_time = max(1, word_count // 200)
            print(f"  - Word count: {word_count}")
            print(f"  - Reading time: ~{reading_time} minutes")

            # Save extracted content
            content_file = OUTPUT_DIR / f"{timestamp}_content.txt"
            content_file.write_text(result.content, encoding="utf-8")
            print(f"\n  ✓ Saved extracted content to: {content_file}")

            # Save metadata
            metadata_file = OUTPUT_DIR / f"{timestamp}_metadata.txt"
            metadata_content = f"""Medium Article Extraction Report
================================

URL: {url}

Metadata:
---------
Title: {result.title}
Author: {result.author}
Published: {result.date_published}
Word Count: {word_count}
Reading Time: ~{reading_time} minutes

HTML Metrics:
-------------
Total HTML size: {html_size:,} characters
Script tags: {script_count}
Div tags: {div_count}
Paragraph tags: {p_count}
Link tags: {a_count}
React detected: {has_react}

Content Preview (first 500 chars):
----------------------------------
{result.content[:500]}...

Status: ✓ Successfully extracted
"""
            metadata_file.write_text(metadata_content, encoding="utf-8")
            print(f"  ✓ Saved metadata report to: {metadata_file}")

            print("\n" + "=" * 80)
            print("TEST COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print(f"\nFiles saved:")
            print(f"  1. Raw HTML: {raw_file.name}")
            print(f"  2. Extracted content: {content_file.name}")
            print(f"  3. Metadata report: {metadata_file.name}")
            print(f"\nLocation: {OUTPUT_DIR}")

        except asyncio.TimeoutError:
            print("\n✗ TEST FAILED!")
            print("Error: Page took too long to load (timeout)")

        except Exception as e:
            print("\n✗ TEST FAILED!")
            print(f"Error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()


async def main():
    """Run the Medium article scraping test."""
    await test_medium_article()


if __name__ == "__main__":
    asyncio.run(main())
