#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting server..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000


