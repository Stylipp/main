from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.features.auth.router.router import router as auth_router
from src.features.storage.router.router import router as storage_router

settings = get_settings()

app = FastAPI(title="Stylipp API", version="1.0.0")

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
