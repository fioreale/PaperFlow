# PaperFlow

Research Paper Management System built with FastAPI.

## Features

- FastAPI backend with automatic API documentation
- Modular project structure
- CORS middleware configured
- Environment-based configuration
- Health check endpoint

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
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PaperFlow
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
```

5. Run the application:
```bash
python -m app.main
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
```

### Linting

```bash
flake8 app/
```

### Type Checking

```bash
mypy app/
```

## License

TBD
