"""Test PDF generation with real URL content from browserless.io."""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.services.pdf_generator import PDFGeneratorService
    from app.services.article_extractor import ArticleExtractorService
except (ImportError, OSError) as e:
    print(f"Error: Could not import required services: {e}")
    sys.exit(1)

# Create output directory for test results
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "pdf_generation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def test_real_url_pdf_generation():
    """Test PDF generation with real content from a URL."""

    url = "https://www.browserless.io/feature/rest-apis"

    print("=" * 80)
    print("PDF GENERATION TEST WITH REAL URL")
    print("=" * 80)
    print(f"\nURL: {url}")
    print(f"Output directory: {OUTPUT_DIR}\n")

    try:
        # Step 1: Extract article content
        print("─" * 80)
        print("STEP 1: Extracting article content")
        print("─" * 80)

        async with ArticleExtractorService() as extractor:
            print(f"Fetching content from URL...")
            article = await extractor.extract_article(url)

            print(f"✓ Content extracted successfully!")
            print(f"\nArticle Details:")
            print(f"  Title: {article.title}")
            print(f"  Author: {article.author or 'Not specified'}")
            print(f"  Date: {article.date_published or 'Not specified'}")
            print(f"  Excerpt: {article.excerpt[:100] if article.excerpt else 'None'}...")
            print(f"  Content length: {len(article.content)} characters")
            print(f"  Content preview (first 200 chars):")
            print(f"  {article.content[:200]}...")

        # Step 2: Generate PDF
        print("\n" + "─" * 80)
        print("STEP 2: Generating PDF")
        print("─" * 80)

        pdf_service = PDFGeneratorService()

        # Generate sanitized filename
        sanitized_filename = pdf_service.sanitize_filename(article.title)
        print(f"\nFilename sanitization:")
        print(f"  Original: {article.title}")
        print(f"  Sanitized: {sanitized_filename}")

        # Generate output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_id = f"real_url_test_{timestamp}"
        output_path = pdf_service.get_output_path(job_id, article.title)

        print(f"\nGeneration details:")
        print(f"  Job ID: {job_id}")
        print(f"  Output path: {output_path}")

        # Generate the PDF
        print(f"\nGenerating PDF...")
        result_path = await pdf_service.generate_pdf(article, output_path)

        # Step 3: Verify output
        print("\n" + "─" * 80)
        print("STEP 3: Verifying PDF output")
        print("─" * 80)

        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"✓ PDF generated successfully!")
            print(f"  File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")

            # Verify PDF validity
            with open(result_path, "rb") as f:
                header = f.read(4)
                is_valid_pdf = header == b"%PDF"

            if is_valid_pdf:
                print(f"✓ Valid PDF file (correct header)")
            else:
                print(f"✗ Invalid PDF file (incorrect header)")
                return False

            # Copy to test output directory
            import shutil
            test_output = OUTPUT_DIR / f"{timestamp}_browserless_rest_apis.pdf"
            shutil.copy(result_path, test_output)
            print(f"✓ Copied to test output: {test_output}")

            # Summary
            print("\n" + "=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)
            print(f"✓ Test completed successfully!")
            print(f"\nDetails:")
            print(f"  Source URL: {url}")
            print(f"  Article title: {article.title}")
            print(f"  Content length: {len(article.content)} characters")
            print(f"  PDF size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
            print(f"  Output file: {test_output}")
            print(f"\n📁 PDF saved to: {test_output}")

            return True

        else:
            print(f"✗ PDF file not created at expected location: {result_path}")
            return False

    except Exception as e:
        print(f"\n✗ TEST FAILED!")
        print(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the real URL PDF generation test."""
    success = await test_real_url_pdf_generation()

    if success:
        print("\n" + "=" * 80)
        print("✓ TEST PASSED")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("✗ TEST FAILED")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
