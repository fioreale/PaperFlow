"""Test script for PDF generation."""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.services.pdf_generator import PDFGeneratorService
    from app.schemas.conversion import ArticleContent
except (ImportError, OSError) as e:
    print(f"Warning: Could not import PDF generation service: {e}")
    print("This test requires WeasyPrint system dependencies.")
    PDFGeneratorService = None
    ArticleContent = None


async def test_pdf_generation():
    """Test PDF generation with sample article content."""
    if PDFGeneratorService is None:
        print("Skipping test_pdf_generation: WeasyPrint dependencies not available")
        return

    service = PDFGeneratorService()

    print("=" * 80)
    print("PDF Generation Test")
    print("=" * 80)
    print(f"Temp directory: {service.env.loader.searchpath[0]}")
    print()

    # Sample article content
    sample_articles = [
        ArticleContent(
            title="Introduction to Python",
            author="John Doe",
            content="<h2>Introduction</h2><p>Python is a high-level programming language...</p>"
            + "<h2>Key Features</h2><p>Python features include simplicity, readability, and extensive libraries.</p>"
            + "<p>It is widely used in web development, data science, and artificial intelligence.</p>",
            excerpt="Learn the basics of Python programming",
            lead_image_url="https://example.com/python.jpg",
            date_published="2025-01-15",
            url="https://example.com/python-intro",
        ),
        ArticleContent(
            title="Web Development with FastAPI",
            author="Jane Smith",
            content="<h2>FastAPI Overview</h2><p>FastAPI is a modern web framework for building APIs with Python.</p>"
            + "<h2>Getting Started</h2><p>FastAPI makes it easy to build REST APIs with automatic documentation.</p>"
            + "<p>It includes built-in support for async/await and data validation.</p>",
            excerpt="Build fast and modern web APIs",
            date_published="2025-01-20",
            url="https://example.com/fastapi-guide",
        ),
    ]

    for i, article in enumerate(sample_articles, 1):
        print(f"\n{'─' * 80}")
        print(f"Test {i}: {article.title}")
        print(f"{'─' * 80}")

        try:
            # Test filename sanitization
            sanitized = service.sanitize_filename(article.title)
            print(f"Original title: {article.title}")
            print(f"Sanitized filename: {sanitized}")

            # Generate output path
            job_id = f"test_job_{i}"
            output_path = service.get_output_path(job_id, article.title)
            print(f"Output path: {output_path}")

            # Generate PDF
            print("\nGenerating PDF...")
            result_path = await service.generate_pdf(article, output_path)

            # Check if file was created
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(f"✓ PDF generated successfully!")
                print(f"  File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
                print(f"  Path: {result_path}")

                # Try to open and verify it's a valid PDF
                with open(result_path, "rb") as f:
                    header = f.read(4)
                    if header == b"%PDF":
                        print(f"  ✓ Valid PDF file (correct header)")
                    else:
                        print(f"  ✗ Invalid PDF file (incorrect header)")
            else:
                print(f"✗ PDF file not created at expected location")

        except Exception as e:
            print(f"✗ PDF generation failed!")
            print(f"Error: {type(e).__name__}: {str(e)}")


def test_filename_sanitization():
    """Test filename sanitization edge cases."""
    if PDFGeneratorService is None:
        print("Skipping test_filename_sanitization: WeasyPrint dependencies not available")
        return

    service = PDFGeneratorService()

    print("\n" + "=" * 80)
    print("Filename Sanitization Tests")
    print("=" * 80)

    test_cases = [
        'Article: "The Best Way" to Learn Python?',
        "File|Name*With<Invalid>Characters",
        "Very " + "Long " * 20 + "Title That Exceeds Maximum Length",
        "   Spaces   Around   Edges   ",
        "...Dots and Dashes...",
        "",
    ]

    for test_input in test_cases:
        result = service.sanitize_filename(test_input)
        print(f"\nInput:  {test_input!r}")
        print(f"Output: {result!r}")


async def main():
    """Run all PDF generation tests."""
    await test_pdf_generation()
    test_filename_sanitization()

    print("\n" + "=" * 80)
    print("PDF Generation Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
