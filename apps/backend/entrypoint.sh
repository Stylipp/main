#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

# Seed products if the database is empty
PRODUCT_COUNT=$(python -c "
import asyncio
from sqlalchemy import text
from src.core.database import engine
async def count():
    async with engine.connect() as conn:
        r = await conn.execute(text('SELECT COUNT(*) FROM products'))
        return r.scalar()
print(asyncio.run(count()))
" 2>/dev/null || echo "0")

if [ "$PRODUCT_COUNT" -eq 0 ] 2>/dev/null; then
    echo "No products found. Running bootstrap seeding..."
    python -m scripts.seed_bootstrap
    echo "Seeding complete."
else
    echo "Found $PRODUCT_COUNT products, skipping seed."
fi

echo "Starting server..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000


