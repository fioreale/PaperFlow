FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint, Playwright and other tools
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
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md .python-version ./
COPY app ./app

# Install Python dependencies directly
RUN pip install --no-cache-dir -e .

# Install Playwright browsers (chromium by default)
RUN playwright install --with-deps chromium

# Create temp directory for PDF generation
RUN mkdir -p /tmp/paperflow

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
