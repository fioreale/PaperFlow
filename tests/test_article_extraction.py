"""Test script for article HTML extraction using Playwright + Trafilatura."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.article_extractor import ArticleExtractorService

# Try to import PDF generator
try:
    from app.services.pdf_generator import PDFGeneratorService
    PDF_AVAILABLE = True
except (ImportError, OSError) as e:
    PDF_AVAILABLE = False
    PDF_ERROR = str(e)

# Create output directory for test results
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


async def test_extraction():
    """Test trafilatura-based extraction with sample URLs."""
    # Test URLs (using commonly stable URLs for testing)
    test_urls = [
        "https://example.com",
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
    ]

    print("=" * 80)
    print("Article Content Extraction Test (Playwright + Trafilatura)")
    print("=" * 80)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Use async context manager for efficient browser reuse
    async with ArticleExtractorService() as service:
        for i, url in enumerate(test_urls, 1):
            print(f"\n{'─' * 80}")
            print(f"Testing URL {i}/{len(test_urls)}: {url}")
            print(f"{'─' * 80}")

            try:
                # Fetch raw HTML
                print(f"\n[STEP 1] Fetching HTML with Playwright...")
                raw_html = await service._fetch_html(url)
                print(f"  ✓ Fetched {len(raw_html)} characters")

                # Save raw HTML
                url_safe = url.replace("https://", "").replace("http://", "").replace("/", "_")[:50]
                raw_file = OUTPUT_DIR / f"{timestamp}_test{i}_{url_safe}_01_raw.html"
                raw_file.write_text(raw_html, encoding="utf-8")
                print(f"  ✓ Saved to: {raw_file}")

                # Extract article
                print(f"\n[STEP 2] Extracting content with Trafilatura...")
                article = await service.extract_article(url)
                print(f"  ✓ Extraction successful!")

                # Save extracted content
                extracted_file = OUTPUT_DIR / f"{timestamp}_test{i}_{url_safe}_02_extracted.html"
                extracted_file.write_text(article.content, encoding="utf-8")
                print(f"  ✓ Saved to: {extracted_file}")

                # Save metadata
                metadata_content = f"""Title: {article.title}
Author: {article.author or 'N/A'}
URL: {article.url}
Date Published: {article.date_published or 'N/A'}
Excerpt: {article.excerpt or 'N/A'}
Lead Image: {article.lead_image_url or 'N/A'}
Content Length: {len(article.content)} characters

Content Preview (first 500 chars):
{article.content[:500]}
"""
                metadata_file = OUTPUT_DIR / f"{timestamp}_test{i}_{url_safe}_03_metadata.txt"
                metadata_file.write_text(metadata_content, encoding="utf-8")
                print(f"  ✓ Saved metadata to: {metadata_file}")

                # Generate PDF
                print(f"\n[STEP 3] Generating PDF...")
                if PDF_AVAILABLE:
                    try:
                        pdf_service = PDFGeneratorService()
                        pdf_file = OUTPUT_DIR / f"{timestamp}_test{i}_{url_safe}_04_final.pdf"
                        await pdf_service.generate_pdf(article, str(pdf_file))
                        print(f"  ✓ PDF generated successfully!")
                        print(f"  ✓ Saved to: {pdf_file}")
                        print(f"    File size: {pdf_file.stat().st_size:,} bytes ({pdf_file.stat().st_size / 1024:.2f} KB)")

                        # Verify PDF
                        with open(pdf_file, "rb") as f:
                            if f.read(4) == b"%PDF":
                                print(f"    ✓ Valid PDF file verified")
                    except Exception as e:
                        print(f"  ⚠️  PDF generation failed: {str(e)}")
                else:
                    print(f"  ⚠️  PDF Generator not available: {PDF_ERROR}")

                print(f"\n✓ Test {i} completed successfully!")
                print(f"  Title: {article.title}")
                print(f"  Content: {len(article.content)} characters")

                reduction = (len(raw_html) - len(article.content)) / len(raw_html) * 100
                print(f"  Content reduction: {reduction:.1f}%")

            except Exception as e:
                print(f"✗ Extraction failed!")
                print(f"Error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()


async def main():
    """Run complete extraction pipeline test: Playwright -> Trafilatura -> PDF."""
    await test_extraction()

    print("\n" + "=" * 80)
    print("PIPELINE TEST COMPLETE")
    print("=" * 80)
    print(f"\n📁 Output files saved to: {OUTPUT_DIR}")
    print("\n📄 Files created (each step of the pipeline):")

    # Group files by test
    files = sorted(OUTPUT_DIR.glob("*"))
    for file in files:
        size = file.stat().st_size
        # Determine file type
        if "_01_raw.html" in file.name:
            file_type = "Playwright HTML"
        elif "_02_extracted.html" in file.name:
            file_type = "Trafilatura Content"
        elif "_03_metadata.txt" in file.name:
            file_type = "Metadata"
        elif "_04_final.pdf" in file.name:
            file_type = "Final PDF"
        else:
            file_type = "Other"

        print(f"  [{file_type:20s}] {file.name} ({size:,} bytes)")

    print("\n✅ Complete pipeline: URL -> Playwright -> Trafilatura -> PDF")
    print("   You can inspect these files to see each transformation step!")


if __name__ == "__main__":
    asyncio.run(main())
