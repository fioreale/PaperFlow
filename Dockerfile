FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint and other tools
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    libcairo2-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Rye
RUN curl -sSf https://rye-up.com/get | RYE_INSTALL_OPTION="--yes" bash && \
    echo 'source "$HOME/.rye/env"' >> ~/.bashrc

ENV PATH="/root/.rye/shims:${PATH}"

# Copy project files
COPY pyproject.toml .python-version ./
COPY app ./app

# Install dependencies
RUN rye sync --no-dev

# Create temp directory for PDF generation
RUN mkdir -p /tmp/paperflow

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["rye", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
