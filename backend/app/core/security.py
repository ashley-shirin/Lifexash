"""Password hashing (bcrypt), JWT access tokens (PyJWT) and the current-user dependency."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import JWT_ALGORITHM, settings
from app.core.database import get_db
from app.models import User

# auto_error=False: we raise our own 401 below, so a missing header and a bad token look the same.
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    # gensalt() makes a random salt per password; the salt is stored inside the hash itself.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # bcrypt rejects passwords over 72 bytes; such a password can never match.
        return False


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),  # JWT spec: "sub" must be a string
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """Return the user id inside a valid token. Raises jwt.InvalidTokenError otherwise (incl. expired)."""
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["exp", "sub"]},
    )
    try:
        return int(payload["sub"])
    except ValueError as exc:
        raise jwt.InvalidTokenError("sub is not a user id") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: add `current_user: User = Depends(get_current_user)` to protect a route."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise unauthorized from None

    user = db.get(User, user_id)
    if user is None:  # token is valid but the account no longer exists
        raise unauthorized
    return user
