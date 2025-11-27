# PaperFlow

Research Paper Management System built with FastAPI.

## Features

- FastAPI backend with automatic API documentation
- Modular project structure
- CORS middleware configured
- Environment-based configuration
- Health check endpoint
- Managed by Rye for streamlined dependency management

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

- [Rye](https://rye-up.com/) - Modern Python package manager
- Python 3.11+

### Installation

1. Install Rye (if not already installed):
```bash
curl -sSf https://rye-up.com/get | bash
```

2. Clone the repository:
```bash
git clone <repository-url>
cd PaperFlow
```

3. Sync dependencies:
```bash
rye sync
```

4. Create environment file:
```bash
cp .env.example .env
```

5. Run the application:
```bash
rye run dev
```

Or start without auto-reload:
```bash
rye run start
```

Or manually with uvicorn:
```bash
rye run uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## Development

### Running Tests

```bash
rye run pytest
```

### Code Formatting

```bash
rye run black app/
```

### Linting

```bash
rye run flake8 app/
```

### Type Checking

```bash
rye run mypy app/
```

### Adding Dependencies

```bash
# Add a runtime dependency
rye add <package-name>

# Add a development dependency
rye add --dev <package-name>

# Sync dependencies
rye sync
```

## License

TBD
