from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.dependencies import get_current_user
from src.features.auth.schemas.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Authenticate a user and return a JWT token.

    Placeholder — returns 501 until authentication logic is implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login not yet implemented",
    )


@router.get("/me")
async def get_me(user_id: UUID = Depends(get_current_user)) -> dict:
    """Return the current authenticated user's info.

    Requires a valid JWT bearer token.
    """
    return {"user_id": str(user_id)}
