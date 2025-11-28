FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint and other tools
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    libcairo2 \
    libcairo2-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md .python-version ./
COPY app ./app

# Install Python dependencies directly
RUN pip install --no-cache-dir -e .

# Create temp directory for PDF generation
RUN mkdir -p /tmp/paperflow

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
