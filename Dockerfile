FROM python:3.11-slim

WORKDIR /app

# Install Rye
RUN curl -sSf https://rye-up.com/get | RYE_INSTALL_OPTION="--yes" bash && \
    echo 'source "$HOME/.rye/env"' >> ~/.bashrc

ENV PATH="/root/.rye/shims:${PATH}"

# Copy project files
COPY pyproject.toml .python-version ./
COPY app ./app

# Install dependencies
RUN rye sync --no-dev

# Expose port
EXPOSE 8000

# Run application
CMD ["rye", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
