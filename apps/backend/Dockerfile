FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared schemas package first and install it
COPY packages/schemas /tmp/schemas
RUN pip install --no-cache-dir /tmp/schemas && rm -rf /tmp/schemas

# Copy backend pyproject.toml and create a modified version without local file reference
COPY apps/backend/pyproject.toml ./pyproject.toml.orig

# Remove the stylipp-schemas file reference (already installed above)
RUN sed 's|"stylipp-schemas @ file:../../packages/schemas",||' pyproject.toml.orig > pyproject.toml

# Install CPU-only PyTorch + torchvision (avoids ~3GB of CUDA dependencies)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install backend dependencies (torch already satisfied, won't re-download)
RUN pip install --no-cache-dir .

# Copy backend source code
COPY apps/backend/src ./src
COPY apps/backend/alembic ./alembic
COPY apps/backend/alembic.ini ./
COPY apps/backend/entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
