# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set work directory
WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml poetry.lock ./

# Install dependencies (Production only)
# This excludes 'dev' group which contains Playwright
RUN poetry install --without dev --no-interaction --no-ansi

# Copy project files (for standalone image builds)
# Note: In development via docker-compose, these will be shadowed by the volume mount
COPY README.md AGENTS.md ./
COPY project ./project
COPY scripts ./scripts

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "project.main:app", "--host", "0.0.0.0", "--port", "8000"]
