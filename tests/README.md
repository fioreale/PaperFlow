# PaperFlow Component Tests

This directory contains standalone test scripts for testing individual components of PaperFlow:

- **HTML Extraction with Trafilatura**
- **PDF Generation**
- **Dropbox Connection & Upload**

## Running the Tests

### Prerequisites

Make sure you have all dependencies installed:

```bash
cd /home/cloudops/external/PaperFlow
rye sync
```

### 1. Test Article HTML Extraction with Trafilatura

**File:** `test_article_extraction.py`

**What it tests:**
- Article content extraction using trafilatura
- HTML parsing and content extraction (title, author, content, etc.)
- Metadata extraction (publication date, excerpt, author, etc.)
- Graceful fallback handling when content extraction is incomplete

**Run the test:**

```bash
python tests/test_article_extraction.py
```

**Optional:** During the test, you can enter a custom URL to test extraction against any real website.

**Expected output:**
- Title, author, date, and content preview for tested URLs
- Error messages if extraction fails

**Notes:**
- Trafilatura uses machine learning-based content extraction
- Works with most news articles and blog posts
- Some URLs may fail to extract - this is normal for structured/non-article content
- Requires internet connectivity to fetch and extract article content

### 2. Test PDF Generation

**File:** `test_pdf_generation.py`

**What it tests:**
- PDF generation from sample article content
- Filename sanitization for various edge cases
- PDF file creation and validity
- WeasyPrint integration
- CSS styling application

**Run the test:**

```bash
python tests/test_pdf_generation.py
```

**Expected output:**
- Test results for multiple sample articles
- Generated PDF file paths and sizes
- PDF header validation (checks for valid PDF magic bytes)
- Filename sanitization test results

**Output files:**
- Generated PDFs are saved to `/tmp/paperflow/` directory
- Files are prefixed with `test_job_` for easy identification

**Notes:**
- The test creates real PDF files
- Files can be manually deleted if needed
- PDF generation uses WeasyPrint with e-ink optimizations

### 3. Test Dropbox Connection

**File:** `test_dropbox_connection.py`

**What it tests:**
- Dropbox token authentication
- Dropbox client initialization
- Folder creation (if needed)
- File upload functionality
- Shared link generation

**Prerequisites:**
- Must have `DROPBOX_ACCESS_TOKEN` environment variable set
- Requires valid Dropbox API credentials

**Run the test:**

```bash
# Set your Dropbox token first
export DROPBOX_ACCESS_TOKEN="your-token-here"

# Then run the test
python tests/test_dropbox_connection.py
```

**Expected output (when configured):**
- ✓ Dropbox client initialization success
- ✓ Folder creation at configured path
- ✓ Test file uploaded successfully with Dropbox path
- ✓ Shared link URL (if applicable)

**Expected output (when not configured):**
- ✗ Dropbox not configured
- Instructions on how to configure it

**Notes:**
- The test creates a small test file and uploads it to Dropbox
- Test files are uploaded to the configured folder (default: `/PaperFlow`)
- You should manually delete test files from Dropbox web interface
- Requires internet connectivity

## Configuration

### Trafilatura (Article Extraction)

No configuration needed - trafilatura works out of the box with no API keys. It uses machine learning-based extraction and works with most URLs automatically.

Optional environment variables (if needed):
```bash
# No API keys required for trafilatura
# It uses open-source ML models for extraction
```

### Dropbox

Set environment variable:
```bash
export DROPBOX_ACCESS_TOKEN="your-dropbox-token"
export DROPBOX_FOLDER_PATH="/PaperFlow"  # Optional, has default
```

Get a Dropbox API token:
1. Go to https://www.dropbox.com/developers/apps
2. Create a new app or select existing app
3. Generate an access token in the app settings

## Running All Tests Together

Create a test runner script or use the individual tests. Only Dropbox requires configuration:

```bash
# Configure Dropbox (optional)
export DROPBOX_ACCESS_TOKEN="your-token"

# Run tests
python tests/test_article_extraction.py
python tests/test_pdf_generation.py
python tests/test_dropbox_connection.py
```

## Interpreting Results

### Success Indicators (✓)
- Article Extraction: Article extraction completes with title and content
- PDF: Files created with valid PDF headers, file size > 0
- Dropbox: Authentication successful, files uploaded with returned paths

### Failure Indicators (✗)
- Article Extraction: Network errors, timeout, empty responses
- PDF: File not created, invalid PDF header, zero file size
- Dropbox: Token invalid, authentication failed, upload errors

## Troubleshooting

### Article Extraction Issues
- **Network timeout**: Check internet connection
- **403 Forbidden**: Some websites block automated access
- **Empty content**: Trafilatura may not extract content for some page types
- **ImportError for trafilatura**: Run `rye sync` to install dependencies

### PDF Generation Issues
- **WeasyPrint not installed**: Run `rye sync`
- **Invalid template path**: Ensure `app/templates/` directory exists
- **Permission denied**: Check `/tmp/paperflow` directory permissions
- **Out of memory**: Some PDFs require significant memory to generate
- **WeasyPrint system dependencies**: Ensure libpango-1.0-0, libcairo, and related libraries are installed

### Dropbox Issues
- **AuthError**: Token is invalid or expired
- **ApiError**: Network issue or Dropbox API problem
- **Folder not found**: Path doesn't exist and client lacks permission to create it
- **File already exists**: Upload with same name - test uses "overwrite" mode

## Cleanup

After testing, you may want to clean up:

```bash
# Remove generated test PDFs
rm -rf /tmp/paperflow/test_*

# Remove uploaded test files from Dropbox (manual via web interface)
# Navigate to /PaperFlow folder and delete test_paperflow_upload.txt
```

## Next Steps

After these individual tests pass:
1. Test the full conversion pipeline with `convert-sync` endpoint
2. Test async conversion with `convert` and `status` endpoints
3. Test with real article URLs from various sources
4. Load testing with multiple concurrent requests
