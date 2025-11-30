"""Test suite for HTML extraction using Playwright.

This test focuses on the first step of the pipeline: fetching and rendering HTML
with JavaScript execution using Playwright.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.article_extractor import ArticleExtractorService

# Create output directory for test results
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "html_extraction"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def test_html_extraction():
    """Test HTML extraction with various URLs and edge cases."""

    test_cases = [
        {
            "name": "Simple Static Site",
            "url": "https://example.com",
            "description": "Basic HTML site without JavaScript",
        },
        {
            "name": "Medium Article",
            "url": "https://medium.com/@alaayedi090/a-journey-through-azure-building-a-domain-controller-syncing-with-entra-connect-and-enhancing-94885a22a7a8",
            "description": "Medium article with heavy JavaScript rendering",
        },
        {
            "name": "Wikipedia Article",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "description": "Wikipedia page with complex content structure",
        },
        {
            "name": "News Article",
            "url": "https://www.bbc.com",
            "description": "News site with dynamic content loading",
        },
        {
            "name": "Blog Post",
            "url": "https://www.w3schools.com/html/",
            "description": "Educational tutorial with code examples",
        },
    ]

    print("=" * 80)
    print("HTML Extraction Test (Playwright)")
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

            print(f"\n{'─' * 80}")
            print(f"Test {i}/{len(test_cases)}: {name}")
            print(f"URL: {url}")
            print(f"Description: {description}")
            print(f"{'─' * 80}")

            try:
                print(f"\n[FETCHING] Retrieving HTML with Playwright...")
                raw_html = await service._fetch_html(url)

                html_size = len(raw_html)
                print(f"  ✓ Successfully fetched {html_size:,} characters")

                # Analyze HTML content
                print(f"\n[ANALYSIS]")

                # Check for common JS frameworks
                has_react = "react" in raw_html.lower()
                has_vue = "vue" in raw_html.lower()
                has_angular = "angular" in raw_html.lower()
                print(f"  React detected: {has_react}")
                print(f"  Vue detected: {has_vue}")
                print(f"  Angular detected: {has_angular}")

                # Check for dynamic loading scripts
                has_script_tags = raw_html.count("<script") > 0
                script_count = raw_html.count("<script")
                print(f"  Script tags found: {script_count}")

                # Save raw HTML
                url_safe = url.replace("https://", "").replace("http://", "").replace("/", "_")[:50]
                raw_file = OUTPUT_DIR / f"{timestamp}_test{i}_{url_safe}_raw.html"
                raw_file.write_text(raw_html, encoding="utf-8")
                print(f"\n  ✓ Saved to: {raw_file}")

                # Save analysis report
                report_file = OUTPUT_DIR / f"{timestamp}_test{i}_{url_safe}_analysis.txt"
                analysis_content = f"""HTML Extraction Analysis Report
================================

Test Case: {name}
URL: {url}
Description: {description}

Metrics:
--------
- Total HTML size: {html_size:,} characters
- Script tags: {script_count}
- React framework: {has_react}
- Vue framework: {has_vue}
- Angular framework: {has_angular}

HTML Structure:
- <html> tags: {raw_html.count("<html")}
- <head> tags: {raw_html.count("<head")}
- <body> tags: {raw_html.count("<body")}
- <div> tags: {raw_html.count("<div")}
- <p> tags: {raw_html.count("<p")}
- <img> tags: {raw_html.count("<img")}
- <a> tags: {raw_html.count("<a")}

Status: ✓ Successfully extracted
"""
                report_file.write_text(analysis_content, encoding="utf-8")
                print(f"  ✓ Analysis saved to: {report_file}")

                results.append({
                    "name": name,
                    "url": url,
                    "success": True,
                    "size": html_size,
                    "scripts": script_count,
                    "error": None,
                })

                print(f"\n✓ Test {i} completed successfully!")

            except asyncio.TimeoutError:
                print(f"✗ Test {i} TIMEOUT!")
                print(f"Error: Page took too long to load (>60 seconds)")
                results.append({
                    "name": name,
                    "url": url,
                    "success": False,
                    "size": 0,
                    "scripts": 0,
                    "error": "Timeout",
                })

            except Exception as e:
                print(f"✗ Test {i} FAILED!")
                print(f"Error: {type(e).__name__}: {str(e)}")
                results.append({
                    "name": name,
                    "url": url,
                    "success": False,
                    "size": 0,
                    "scripts": 0,
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

    print(f"\nDetailed Results:")
    print(f"{'Test':<20} {'Status':<12} {'Size (KB)':<12} {'Scripts':<10}")
    print(f"{'-' * 54}")
    for result in results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        size_kb = f"{result['size'] / 1024:.2f}" if result["size"] > 0 else "N/A"
        print(f"{result['name']:<20} {status:<12} {size_kb:<12} {result['scripts']:<10}")

    print(f"\n📁 Output files saved to: {OUTPUT_DIR}")
    print(f"   - Raw HTML files (*_raw.html)")
    print(f"   - Analysis reports (*_analysis.txt)")


async def main():
    """Run HTML extraction tests."""
    await test_html_extraction()


if __name__ == "__main__":
    asyncio.run(main())
