FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared schemas package first (backend depends on it)
COPY packages/schemas /tmp/schemas

# Copy backend requirements
COPY apps/backend/pyproject.toml ./

# Install schemas package, then backend dependencies
RUN pip install --no-cache-dir /tmp/schemas && \
    pip install --no-cache-dir . && \
    rm -rf /tmp/schemas

# Copy backend source code
COPY apps/backend/src ./src
COPY apps/backend/alembic ./alembic
COPY apps/backend/alembic.ini ./

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
