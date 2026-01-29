from src.models.user import User


async def authenticate_user(email: str, password: str) -> User | None:
    """Authenticate a user by email and password.

    Placeholder implementation — will be completed in a later phase
    when password hashing and database queries are wired up.
    """
    return None
