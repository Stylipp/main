from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.features.auth.utils.jwt import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> UUID:
    """Extract and verify the current user from the JWT bearer token."""
    return verify_token(token)
