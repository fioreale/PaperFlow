"""Test suite for article content extraction using Trafilatura.

This test focuses on the second step of the pipeline: extracting meaningful
article content from HTML using Trafilatura with various content structures.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.article_extractor import ArticleExtractorService

# Create output directory for test results
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "content_extraction"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def test_content_extraction():
    """Test content extraction from various article types."""

    test_cases = [
        {
            "name": "Simple Article",
            "url": "https://example.com",
            "expected_content_type": "basic",
            "description": "Simple HTML without complex structure",
        },
        {
            "name": "Long-form Article",
            "url": "https://medium.com/@alaayedi090/a-journey-through-azure-building-a-domain-controller-syncing-with-entra-connect-and-enhancing-94885a22a7a8",
            "expected_content_type": "long-form",
            "description": "In-depth technical article with multiple sections",
        },
        {
            "name": "Structured Content",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "expected_content_type": "structured",
            "description": "Content with headers, lists, and tables",
        },
        {
            "name": "News Article",
            "url": "https://www.bbc.com",
            "expected_content_type": "news",
            "description": "News article with author, date, and structured body",
        },
        {
            "name": "Tutorial/Guide",
            "url": "https://www.w3schools.com/html/",
            "expected_content_type": "guide",
            "description": "Educational content with examples and code",
        },
    ]

    print("=" * 80)
    print("Article Content Extraction Test (Trafilatura)")
    print("=" * 80)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    # Use async context manager for efficient browser reuse
    async with ArticleExtractorService() as service:
        for i, test_case in enumerate(test_cases, 1):
            url = test_case["url"]
            name = test_case["name"]
            description = test_case["description"]
            expected_type = test_case["expected_content_type"]

            print(f"\n{'─' * 80}")
            print(f"Test {i}/{len(test_cases)}: {name}")
            print(f"URL: {url}")
            print(f"Description: {description}")
            print(f"Expected content type: {expected_type}")
            print(f"{'─' * 80}")

            try:
                print(f"\n[EXTRACTING] Processing article content...")
                article = await service.extract_article(url)

                print(f"  ✓ Extraction successful!")

                # Analyze extracted content
                print(f"\n[METADATA]")
                print(f"  Title: {article.title}")
                print(f"  Author: {article.author or 'N/A'}")
                print(f"  Date: {article.date_published or 'N/A'}")
                print(f"  URL: {article.url}")
                print(f"  Excerpt: {article.excerpt[:100] + '...' if article.excerpt and len(article.excerpt) > 100 else article.excerpt or 'N/A'}")

                content_size = len(article.content)
                print(f"\n[CONTENT ANALYSIS]")
                print(f"  Content size: {content_size:,} characters")
                print(f"  Content size: {content_size / 1024:.2f} KB")

                # HTML structure analysis
                h1_count = article.content.count("<h1")
                h2_count = article.content.count("<h2")
                h3_count = article.content.count("<h3")
                p_count = article.content.count("<p")
                img_count = article.content.count("<img")
                table_count = article.content.count("<table")
                link_count = article.content.count("<a ")

                print(f"\n[CONTENT STRUCTURE]")
                print(f"  Headers (H1): {h1_count}")
                print(f"  Headers (H2): {h2_count}")
                print(f"  Headers (H3): {h3_count}")
                print(f"  Paragraphs: {p_count}")
                print(f"  Images: {img_count}")
                print(f"  Tables: {table_count}")
                print(f"  Links: {link_count}")

                # Save extracted content
                url_safe = url.replace("https://", "").replace("http://", "").replace("/", "_")[:50]
                content_file = OUTPUT_DIR / f"{timestamp}_test{i}_{url_safe}_extracted.html"
                content_file.write_text(article.content, encoding="utf-8")
                print(f"\n  ✓ Content saved to: {content_file}")

                # Save metadata and analysis
                analysis_file = OUTPUT_DIR / f"{timestamp}_test{i}_{url_safe}_metadata.txt"
                metadata_content = f"""Article Content Extraction Report
===================================

Test Case: {name}
URL: {url}
Description: {description}

Metadata:
---------
Title: {article.title}
Author: {article.author or 'N/A'}
Date Published: {article.date_published or 'N/A'}
Excerpt: {article.excerpt or 'N/A'}
Lead Image: {article.lead_image_url or 'N/A'}

Content Metrics:
----------------
- Total size: {content_size:,} characters ({content_size / 1024:.2f} KB)
- Headings (H1): {h1_count}
- Headings (H2): {h2_count}
- Headings (H3): {h3_count}
- Paragraphs: {p_count}
- Images: {img_count}
- Tables: {table_count}
- Links: {link_count}

Content Quality Indicators:
---------------------------
- Avg paragraph length: {(content_size // (p_count + 1)) if p_count > 0 else 0} chars
- Has structure (headers): {h1_count + h2_count + h3_count > 0}
- Has media (images): {img_count > 0}
- Has tables: {table_count > 0}
- Has hyperlinks: {link_count > 0}

Content Preview (first 500 characters):
---------------------------------------
{article.content[:500]}

Status: ✓ Successfully extracted
"""
                analysis_file.write_text(metadata_content, encoding="utf-8")
                print(f"  ✓ Analysis saved to: {analysis_file}")

                results.append({
                    "name": name,
                    "url": url,
                    "success": True,
                    "title": article.title,
                    "content_size": content_size,
                    "author": article.author,
                    "date": article.date_published,
                    "paragraphs": p_count,
                    "error": None,
                })

                print(f"\n✓ Test {i} completed successfully!")

            except Exception as e:
                print(f"✗ Test {i} FAILED!")
                print(f"Error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()

                results.append({
                    "name": name,
                    "url": url,
                    "success": False,
                    "title": None,
                    "content_size": 0,
                    "author": None,
                    "date": None,
                    "paragraphs": 0,
                    "error": str(e),
                })

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])

    print(f"\nTotal tests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if successful > 0:
        avg_size = sum(r["content_size"] for r in results if r["success"]) / successful
        avg_paragraphs = sum(r["paragraphs"] for r in results if r["success"]) / successful
        print(f"\nAverage content size: {avg_size:,.0f} characters ({avg_size / 1024:.2f} KB)")
        print(f"Average paragraphs: {avg_paragraphs:.0f}")

    print(f"\nDetailed Results:")
    print(f"{'Test':<20} {'Status':<12} {'Size (KB)':<12} {'Author':<15} {'Date':<12}")
    print(f"{'-' * 71}")
    for result in results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        size_kb = f"{result['content_size'] / 1024:.2f}" if result["content_size"] > 0 else "N/A"
        author = result["author"][:14] if result["author"] else "N/A"
        date = result["date"][:12] if result["date"] else "N/A"
        print(f"{result['name']:<20} {status:<12} {size_kb:<12} {author:<15} {date:<12}")

    print(f"\n📁 Output files saved to: {OUTPUT_DIR}")
    print(f"   - Extracted content (*_extracted.html)")
    print(f"   - Metadata reports (*_metadata.txt)")


async def main():
    """Run article content extraction tests."""
    await test_content_extraction()


if __name__ == "__main__":
    asyncio.run(main())
