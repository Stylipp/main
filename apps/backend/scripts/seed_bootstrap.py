#!/usr/bin/env python3
"""
Bootstrap store seeding script.

Seeds the database with products from a WooCommerce store for MVP development.
Fetches real products via WooCommerce REST API, transforms them, and runs
each through the full ingestion pipeline (quality gate + embedding + storage).

Usage:
    cd apps/backend
    python -m scripts.seed_bootstrap
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.core.qdrant import ensure_collection, get_qdrant_client
from src.features.ai.service.embedding_service import EmbeddingService
from src.features.ai.service.quality_gate import QualityGateService
from src.features.products.service.ingestion_service import IngestionService
from src.features.products.service.product_repository import ProductRepository
from src.features.products.service.transformer import ProductTransformer
from src.features.products.service.woocommerce_client import WooCommerceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STORE_ID = "woo-cloudways"


async def seed_from_woocommerce() -> None:
    """Fetch products from WooCommerce store and ingest them."""
    settings = get_settings()

    # Validate WooCommerce config
    if not all([settings.woo_store_url, settings.woo_consumer_key, settings.woo_consumer_secret]):
        logger.error(
            "WooCommerce credentials not configured. "
            "Set WOO_STORE_URL, WOO_CONSUMER_KEY, WOO_CONSUMER_SECRET in .env"
        )
        return

    # Setup WooCommerce client
    woo_client = WooCommerceClient(
        store_url=settings.woo_store_url,
        consumer_key=settings.woo_consumer_key,
        consumer_secret=settings.woo_consumer_secret,
    )

    # Health check
    if not await woo_client.health_check():
        logger.error("Cannot reach WooCommerce store at %s", settings.woo_store_url)
        return

    product_count = await woo_client.get_product_count()
    logger.info("WooCommerce store has %d published products", product_count)

    # Setup database
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Setup services
    logger.info("Loading FashionSigLIP model (may take a moment on first run)...")
    embedding_service = EmbeddingService()
    embedding_service.load_model()

    quality_gate = QualityGateService()

    await ensure_collection()
    qdrant_client = await get_qdrant_client()

    transformer = ProductTransformer(store_id=STORE_ID)

    # Fetch and ingest products
    success_count = 0
    fail_count = 0
    skipped_count = 0
    total_fetched = 0

    async with async_session() as session:
        repository = ProductRepository(session)
        ingestion_service = IngestionService(
            repository=repository,
            embedding_service=embedding_service,
            quality_gate=quality_gate,
            qdrant_client=qdrant_client,
        )

        async for woo_product in woo_client.get_all_products(per_page=100):
            total_fetched += 1

            # Transform WooProduct → ProductCreate
            product = transformer.transform(woo_product)
            if product is None:
                skipped_count += 1
                logger.debug("Skipped WooCommerce product %d: invalid data", woo_product.id)
                continue

            # Ingest through full pipeline
            result = await ingestion_service.ingest_product(product)

            if result.success:
                success_count += 1
            else:
                fail_count += 1
                if result.quality_issues:
                    logger.debug("Quality rejected %s: %s", product.external_id, result.quality_issues)
                elif result.error == "Product already exists":
                    logger.debug("Duplicate skipped: %s", product.external_id)
                else:
                    logger.warning("Failed %s: %s", product.external_id, result.error)

            processed = success_count + fail_count + skipped_count
            if processed % 50 == 0:
                await session.commit()
                logger.info(
                    "Progress: %d/%d fetched (success: %d, failed: %d, skipped: %d)",
                    processed, product_count, success_count, fail_count, skipped_count,
                )

        await session.commit()

    logger.info(
        "Seeding complete: %d fetched, %d ingested, %d failed, %d skipped (invalid data)",
        total_fetched, success_count, fail_count, skipped_count,
    )

    # Verify Qdrant count
    collection_info = await qdrant_client.get_collection(collection_name="products")
    logger.info("Qdrant products collection: %d vectors", collection_info.points_count)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_from_woocommerce())
