# PaperFlow

Automated Web Article to PDF Conversion System for reMarkable Tablets.

## Overview

PaperFlow is a containerized microservice that converts web articles into optimized PDFs for reMarkable e-ink devices. The system uses FastAPI as the API gateway, trafilatura for Python-based content extraction, WeasyPrint for PDF rendering, and Dropbox for device synchronization.

## Features

- **Article Extraction**: Automatically extracts clean content from web articles
- **E-ink Optimized PDFs**: Custom CSS styling for optimal readability on reMarkable tablets
- **Dropbox Integration**: Seamless synchronization with reMarkable cloud service
- **Asynchronous Processing**: Background job processing for responsive API
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **API Authentication**: Secure API key-based authentication
- **Docker Support**: Fully containerized for easy deployment
- **Scalable Architecture**: Horizontal scaling capability with Redis
- **Managed by UV**: Fast, modern Python package and project manager

## Project Structure

```
PaperFlow/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/          # API route handlers
│   │       ├── __init__.py
│   │       └── health.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Application configuration
│   ├── models/              # Database models
│   │   └── __init__.py
│   ├── schemas/             # Pydantic schemas
│   │   └── __init__.py
│   └── services/            # Business logic
│       └── __init__.py
├── pyproject.toml
├── .python-version
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### Prerequisites

- [UV](https://docs.astral.sh/uv/) - Fast Python package and project manager
- Python 3.11+

### Installation

1. Install UV (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone <repository-url>
cd PaperFlow
```

3. Sync dependencies:
```bash
uv sync
```

4. Create environment file:
```bash
cp .env.example .env
```

5. Run the application:
```bash
uv run uvicorn app.main:app --reload
```

Or for production:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

### API Endpoints

#### POST /api/v1/convert
Submit an article URL for conversion to PDF.

**Request:**
```json
{
  "url": "https://example.com/article",
  "title": "Optional Custom Title",
  "upload_to_dropbox": true
}
```

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "pending",
  "message": "Conversion job created successfully",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### GET /api/v1/status/{job_id}
Check the status of a conversion job.

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "completed",
  "url": "https://example.com/article",
  "title": "Article Title",
  "pdf_path": "/tmp/paperflow/abc123_Article_Title.pdf",
  "dropbox_path": "/PaperFlow/Article_Title.pdf",
  "error": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:45Z",
  "completed_at": "2025-01-15T10:30:45Z"
}
```

### Usage Examples

#### Using cURL

```bash
# Convert an article (async)
curl -X POST "http://localhost:8000/api/v1/convert" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "url": "https://example.com/article",
    "upload_to_dropbox": true
  }'

# Check job status
curl "http://localhost:8000/api/v1/status/abc123-def456-ghi789" \
  -H "X-API-Key: your-api-key-here"
```

#### Using Python

```python
import requests

API_URL = "http://localhost:8000/api/v1"
API_KEY = "your-api-key-here"

headers = {"X-API-Key": API_KEY}

# Submit conversion job
response = requests.post(
    f"{API_URL}/convert",
    json={
        "url": "https://example.com/article",
        "upload_to_dropbox": True
    },
    headers=headers
)
job_data = response.json()
job_id = job_data["job_id"]

# Check status
status_response = requests.get(
    f"{API_URL}/status/{job_id}",
    headers=headers
)
print(status_response.json())
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black app/
```

### Linting

```bash
uv run ruff check app/
```

To automatically fix issues:
```bash
uv run ruff check --fix app/
```

### Type Checking

```bash
uv run mypy app/
```

### Adding Dependencies

```bash
# Add a runtime dependency
uv add <package-name>

# Add a development dependency
uv add --group dev <package-name>

# Sync dependencies
uv sync
```

## Docker Deployment

### Using Docker Compose (Recommended)

1. Create a `.env` file from the example:
```bash
cp .env.example .env
# Edit .env with your configuration
```

2. Build and run the services:
```bash
docker-compose up -d
```

3. View logs:
```bash
docker-compose logs -f api
```

4. Stop services:
```bash
docker-compose down
```

### Using Docker Only

```bash
# Build image
docker build -t paperflow:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e API_KEY=your-api-key \
  -e DROPBOX_ACCESS_TOKEN=your-token \
  --name paperflow \
  paperflow:latest
```

## Configuration

### Required Configuration

- `API_KEY`: Your API key for authentication (change default in production!)

### Optional Configuration

#### Dropbox Integration

To enable automatic PDF upload to Dropbox:

1. Create a Dropbox App at https://www.dropbox.com/developers/apps
2. Configure the app with the following permissions:
   - **files.metadata.read** - Required to check if folders exist
   - **files.content.write** - Required to upload PDF files
   - **files.content.read** - Optional, for reading uploaded files
   - **sharing.write** - Optional, for creating shared links
3. Generate a never-expiring access token:
   - Go to App Console → Settings → "Generate access token"
4. Set the token in your `.env` file:
   ```
   DROPBOX_ACCESS_TOKEN=your-token-here
   DROPBOX_FOLDER_PATH=/PaperFlow
   ```
5. Test the connection:
   ```bash
   uv run python tests/test_dropbox_connection.py
   ```

**Note**: The access token generated from the App Console is scoped to your account only and never expires (unless manually revoked).

See `.env.example` for all available configuration options.

## Architecture

### System Components

- **FastAPI Service**: API gateway and orchestration
- **Trafilatura**: Python-based content extraction from web pages
- **WeasyPrint**: HTML to PDF conversion engine
- **Dropbox Integration**: Cloud storage connector
- **Redis**: Message broker for async processing (optional)

### Data Flow

1. Client submits article URL via POST /api/v1/convert
2. FastAPI creates job and processes in background
3. Trafilatura extracts clean content from the HTML
4. WeasyPrint renders PDF with e-ink optimized styling
5. PDF uploaded to Dropbox (if configured)
6. Client checks status via GET /api/v1/status/{job_id}

## Security

- **API Authentication**: All endpoints require `X-API-Key` header
- **Rate Limiting**: 100 requests per minute per IP by default
- **Input Validation**: Strict URL validation via Pydantic
- **TLS Encryption**: Use HTTPS in production
- **Docker Secrets**: Store credentials securely

## Troubleshooting

### WeasyPrint Dependencies

If you encounter font rendering issues:
```bash
# Debian/Ubuntu
apt-get install libpango-1.0-0 libpangoft2-1.0-0 fonts-liberation

# macOS
brew install pango cairo
```

### Dropbox Connection Issues

**Permission Errors**: If you see errors like "not permitted to access this endpoint":
1. Go to your Dropbox App Console → Permissions tab
2. Enable the required scopes:
   - `files.metadata.read`
   - `files.content.write`
   - `sharing.write` (optional)
3. Click "Submit" to save the permission changes
4. Generate a new access token (old tokens won't have the new permissions)
5. Update your `.env` file with the new token

**Other Issues**:
1. Verify access token is valid
2. Check folder path exists: `/PaperFlow`
3. Run the test script: `uv run python tests/test_dropbox_connection.py`

### PDF Generation Errors

- Check temp directory exists and is writable
- Verify system fonts are installed
- Check WeasyPrint dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

TBD
