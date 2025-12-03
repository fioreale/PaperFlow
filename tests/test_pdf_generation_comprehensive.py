"""Comprehensive test suite for PDF generation using WeasyPrint.

This test focuses on the final step of the pipeline: generating professional PDFs
from article content with various content types and edge cases.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

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

# Create output directory for test results
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "pdf_generation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_filename_sanitization():
    """Test filename sanitization with various edge cases."""
    if PDFGeneratorService is None:
        print("Skipping filename sanitization tests: WeasyPrint dependencies not available")
        return

    service = PDFGeneratorService()

    print("\n" + "=" * 80)
    print("Filename Sanitization Tests")
    print("=" * 80)

    test_cases = [
        {
            "input": "Normal Article Title",
            "description": "Standard filename",
        },
        {
            "input": 'Article: "The Best Way" to Learn Python?',
            "description": "Title with quotes and special punctuation",
        },
        {
            "input": "File|Name*With<Invalid>Characters",
            "description": "Title with filesystem-invalid characters",
        },
        {
            "input": "Very " + "Long " * 20 + "Title That Exceeds Maximum Length Limit",
            "description": "Very long title that needs truncation",
        },
        {
            "input": "   Spaces   Around   Edges   ",
            "description": "Title with excessive whitespace",
        },
        {
            "input": "...Dots and Dashes...",
            "description": "Title with leading/trailing special chars",
        },
        {
            "input": "/Path/Like/Title",
            "description": "Title with forward slashes",
        },
        {
            "input": "C:\\Windows\\Path\\Title",
            "description": "Title with backslashes (Windows path)",
        },
        {
            "input": "",
            "description": "Empty title",
        },
        {
            "input": "   ",
            "description": "Whitespace-only title",
        },
        {
            "input": "Title\nWith\nNewlines",
            "description": "Title with newline characters",
        },
        {
            "input": "Title\tWith\tTabs",
            "description": "Title with tab characters",
        },
    ]

    print(f"\nTesting {len(test_cases)} edge cases...\n")

    for i, test_case in enumerate(test_cases, 1):
        input_title = test_case["input"]
        description = test_case["description"]

        result = service.sanitize_filename(input_title)

        # Validate result
        is_valid = _validate_filename(result)
        status = "✓" if is_valid else "✗"

        print(f"{status} Test {i}: {description}")
        print(f"  Input:  {input_title!r}")
        print(f"  Output: {result!r}")
        print(f"  Valid:  {is_valid}")
        print()

    print(f"✓ All filename sanitization tests completed!")


def _validate_filename(filename: str) -> bool:
    """Validate if filename is safe for filesystem."""
    if not filename:
        return False

    # Check for invalid characters (Windows and Unix)
    invalid_chars = '<>:"|?*\0\n\t'
    for char in invalid_chars:
        if char in filename:
            return False

    # Check for reserved names on Windows
    reserved = [
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    ]

    basename = filename.split(".")[0].upper()
    if basename in reserved:
        return False

    # Must have .pdf extension and not be empty
    if not filename.endswith(".pdf"):
        return False

    return True


async def test_pdf_generation():
    """Test PDF generation with various article content types."""
    if PDFGeneratorService is None:
        print("Skipping PDF generation tests: WeasyPrint dependencies not available")
        return

    service = PDFGeneratorService()

    print("\n" + "=" * 80)
    print("PDF Generation Tests - Content Variations")
    print("=" * 80)
    print(f"Output directory: {OUTPUT_DIR}\n")

    test_cases = [
        {
            "name": "Simple Article",
            "title": "Introduction to Python",
            "author": "John Doe",
            "date": "2025-01-15",
            "url": "https://example.com/python-intro",
            "excerpt": "Learn the basics of Python programming",
            "content": "<h2>Introduction</h2>"
            "<p>Python is a high-level programming language that emphasizes code readability.</p>"
            "<h2>Key Features</h2>"
            "<p>Python features include simplicity, readability, and extensive libraries.</p>"
            "<p>It is widely used in web development, data science, and artificial intelligence.</p>",
            "description": "Simple article with basic HTML structure",
        },
        {
            "name": "Long-form Article",
            "title": "Advanced Python: Async/Await Patterns and Best Practices",
            "author": "Jane Smith",
            "date": "2025-01-20",
            "url": "https://example.com/python-async",
            "excerpt": "Master asynchronous programming in Python",
            "content": "<h2>What is Async?</h2>"
            "<p>Asynchronous programming allows multiple operations to run concurrently.</p>"
            + "<h2>Async/Await Syntax</h2>"
            + "<p>The async/await keywords provide a clean syntax for asynchronous code.</p>"
            + "<p>Key points:</p><ul><li>Use async def for coroutines</li><li>Use await for coroutines</li><li>Handle exceptions properly</li></ul>"
            + "<h2>Real-world Example</h2>"
            + "<p>Here's a practical example of fetching multiple URLs concurrently:</p>"
            + "<pre><code>async def fetch_urls():\n    tasks = [fetch(url) for url in urls]\n    results = await asyncio.gather(*tasks)</code></pre>"
            + ("<p>More content...</p>" * 10),
            "description": "Long-form article with multiple sections, lists, and code blocks",
        },
        {
            "name": "Article with Tables",
            "title": "Comparison of Web Frameworks",
            "author": "Alex Johnson",
            "date": "2025-01-10",
            "url": "https://example.com/web-frameworks",
            "excerpt": "Compare popular Python web frameworks",
            "content": "<h2>Framework Comparison</h2>"
            "<p>Here's a detailed comparison of popular web frameworks:</p>"
            "<table border='1'>"
            "<tr><th>Framework</th><th>Type</th><th>Performance</th><th>Learning Curve</th></tr>"
            "<tr><td>Django</td><td>Full-stack</td><td>Good</td><td>Medium</td></tr>"
            "<tr><td>FastAPI</td><td>Micro</td><td>Excellent</td><td>Low</td></tr>"
            "<tr><td>Flask</td><td>Micro</td><td>Good</td><td>Low</td></tr>"
            "<tr><td>Tornado</td><td>Async</td><td>Excellent</td><td>Medium</td></tr>"
            "</table>"
            "<p>Each framework has its own strengths and use cases.</p>",
            "description": "Article with formatted tables for data comparison",
        },
        {
            "name": "Technical Documentation",
            "title": "API Documentation: User Management Endpoints",
            "author": "Tech Docs Team",
            "date": "2025-01-25",
            "url": "https://example.com/api-docs",
            "excerpt": "Complete API reference for user management",
            "content": "<h2>GET /users</h2>"
            "<p>Retrieve a list of users with pagination support.</p>"
            "<p><strong>Parameters:</strong></p>"
            "<ul><li>page (integer): Page number, default 1</li>"
            "<li>limit (integer): Items per page, default 20</li>"
            "<li>sort (string): Sort field, default 'id'</li></ul>"
            "<p><strong>Response:</strong></p>"
            "<pre><code>{"
            "\"users\": ["
            "{\"id\": 1, \"name\": \"John\", \"email\": \"john@example.com\"}"
            "],"
            "\"total\": 100,"
            "\"page\": 1"
            "}</code></pre>"
            "<h2>POST /users</h2>"
            "<p>Create a new user account.</p>"
            "<p><strong>Request Body:</strong></p>"
            "<pre><code>{"
            "\"name\": \"Jane\","
            "\"email\": \"jane@example.com\","
            "\"password\": \"secure_password\""
            "}</code></pre>",
            "description": "Technical documentation with code snippets and API details",
        },
        {
            "name": "Article with No Author or Date",
            "title": "Anonymous Post: Thoughts on Technology",
            "author": None,
            "date": None,
            "url": "https://example.com/anonymous",
            "excerpt": None,
            "content": "<h2>Introduction</h2>"
            "<p>This is an interesting article without author or publication date information.</p>"
            "<p>The PDF generator should handle missing metadata gracefully.</p>",
            "description": "Article with missing metadata fields",
        },
        {
            "name": "Rich Content with Images",
            "title": "Visual Guide to Web Design",
            "author": "Design Expert",
            "date": "2025-01-18",
            "url": "https://example.com/web-design-guide",
            "excerpt": "Learn web design principles with visual examples",
            "content": "<h2>Color Theory</h2>"
            "<p>Understanding color theory is essential for web design.</p>"
            "<img src='https://example.com/color-wheel.jpg' alt='Color Wheel' width='300'>"
            "<p>The color wheel helps designers choose harmonious color schemes.</p>"
            "<h2>Typography</h2>"
            "<p>Good typography makes content readable and professional.</p>"
            "<img src='https://example.com/typography.jpg' alt='Typography Example'>"
            "<p>Choose fonts that match your brand and ensure good contrast.</p>",
            "description": "Article with images and visual content",
        },
        {
            "name": "Very Long Title Test",
            "title": "A Comprehensive Guide to Understanding, Implementing, and Optimizing Microservices Architecture in Modern Cloud-Native Applications with Best Practices and Real-World Examples",
            "author": "Architecture Team",
            "date": "2025-01-22",
            "url": "https://example.com/long-title",
            "excerpt": "Everything you need to know about microservices",
            "content": "<p>This article tests handling of very long titles in PDF generation.</p>",
            "description": "Article with extremely long title",
        },
    ]

    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, test_case in enumerate(test_cases, 1):
        name = test_case["name"]
        title = test_case["title"]
        description = test_case["description"]

        print(f"\n{'─' * 80}")
        print(f"Test {i}/{len(test_cases)}: {name}")
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"{'─' * 80}")

        try:
            # Create ArticleContent object
            article = ArticleContent(
                title=title,
                author=test_case["author"],
                content=test_case["content"],
                excerpt=test_case["excerpt"],
                lead_image_url=None,
                date_published=test_case["date"],
                url=test_case["url"],
            )

            # Test filename sanitization
            sanitized = service.sanitize_filename(title)
            print(f"\n[SANITIZATION]")
            print(f"  Original: {title}")
            print(f"  Sanitized: {sanitized}")

            # Generate output path
            job_id = f"test_{timestamp}_{i:02d}"
            output_path = service.get_output_path(job_id, title)
            print(f"\n[GENERATION]")
            print(f"  Job ID: {job_id}")
            print(f"  Output path: {output_path}")

            # Generate PDF
            print(f"  Generating PDF...")
            result_path = await service.generate_pdf(article, output_path)

            # Verify file was created
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(f"  ✓ PDF generated successfully!")
                print(f"  File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")

                # Verify PDF validity
                with open(result_path, "rb") as f:
                    header = f.read(4)
                    is_valid = header == b"%PDF"

                if is_valid:
                    print(f"  ✓ Valid PDF file (correct header)")
                else:
                    print(f"  ✗ Invalid PDF file (incorrect header)")

                # Copy to test output directory
                import shutil
                test_output = OUTPUT_DIR / f"{timestamp}_test{i}_{name.replace(' ', '_')}.pdf"
                shutil.copy(result_path, test_output)
                print(f"  ✓ Copied to: {test_output}")

                results.append({
                    "name": name,
                    "success": True,
                    "size": file_size,
                    "title_length": len(title),
                    "error": None,
                })

                print(f"\n✓ Test {i} completed successfully!")

            else:
                print(f"  ✗ PDF file not created at expected location")
                results.append({
                    "name": name,
                    "success": False,
                    "size": 0,
                    "title_length": len(title),
                    "error": "File not created",
                })

        except Exception as e:
            print(f"✗ Test {i} FAILED!")
            print(f"Error: {type(e).__name__}: {str(e)}")

            results.append({
                "name": name,
                "success": False,
                "size": 0,
                "title_length": len(title),
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
        avg_size = sum(r["size"] for r in results if r["success"]) / successful
        print(f"\nAverage PDF size: {avg_size:,.0f} bytes ({avg_size / 1024:.2f} KB)")

    print(f"\nDetailed Results:")
    print(f"{'Test':<30} {'Status':<12} {'Size (KB)':<12} {'Title Length':<15}")
    print(f"{'-' * 69}")
    for result in results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        size_kb = f"{result['size'] / 1024:.2f}" if result["size"] > 0 else "N/A"
        print(f"{result['name']:<30} {status:<12} {size_kb:<12} {result['title_length']:<15}")

    print(f"\n📁 Output PDFs saved to: {OUTPUT_DIR}")


async def main():
    """Run comprehensive PDF generation tests."""
    print("=" * 80)
    print("COMPREHENSIVE PDF GENERATION TEST SUITE")
    print("=" * 80)

    # Run filename sanitization tests (sync)
    test_filename_sanitization()

    # Run PDF generation tests (async)
    await test_pdf_generation()

    print("\n" + "=" * 80)
    print("COMPLETE TEST SUITE FINISHED")
    print("=" * 80)
    print(f"\n📁 All test outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
