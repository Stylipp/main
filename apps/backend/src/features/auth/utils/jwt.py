from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from jose import JWTError, jwt

ALGORITHM = "ES256"
DEFAULT_EXPIRE_DAYS = 15

# Resolve key paths relative to this file's location
# In local dev: apps/backend/secrets/jwt/
# In Docker: /app/secrets/jwt/ (volume mount)
_secrets_dir = Path(__file__).resolve().parents[4] / "secrets" / "jwt"

_private_key_path = _secrets_dir / "private.pem"
_public_key_path = _secrets_dir / "public.pem"


def _load_private_key() -> str:
    return _private_key_path.read_text()


def _load_public_key() -> str:
    return _public_key_path.read_text()


def create_access_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given user."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=DEFAULT_EXPIRE_DAYS))

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
    }

    private_key = _load_private_key()
    return jwt.encode(payload, private_key, algorithm=ALGORITHM)


def verify_token(token: str) -> UUID:
    """Decode and verify a JWT token, returning the user_id (sub claim).

    Raises HTTPException 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        public_key = _load_public_key()
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        return UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
