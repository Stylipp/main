import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.features.ai.router.router import router as ai_router
from src.features.ai.service.embedding_service import EmbeddingService
from src.features.auth.router.router import router as auth_router
from src.features.storage.router.router import router as storage_router

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Load the FashionSigLIP embedding model
    - Shutdown: Cleanup resources
    """
    # Startup
    logger.info("Starting Stylipp API...")

    # Initialize and load embedding service
    embedding_service = EmbeddingService(max_concurrent=4)

    start_time = time.time()
    try:
        embedding_service.load_model()
        load_time = time.time() - start_time
        logger.info("Embedding model loaded in %.2f seconds", load_time)
    except Exception:
        logger.exception("Failed to load embedding model - service will be degraded")
        # Continue startup even if model fails to load
        # Health endpoint will report degraded status

    app.state.embedding_service = embedding_service

    yield

    # Shutdown
    logger.info("Shutting down Stylipp API...")
    # Cleanup if needed (model will be garbage collected)


app = FastAPI(
    title="Stylipp API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


# Feature routers
app.include_router(auth_router, prefix="/api")
app.include_router(storage_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
