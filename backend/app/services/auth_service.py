from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == _normalize_email(email)))


def register(db: Session, data: RegisterIn) -> User:
    email = _normalize_email(data.email)
    email_taken = HTTPException(status.HTTP_409_CONFLICT, "Email is already registered")

    if get_user_by_email(db, email) is not None:
        raise email_taken

    user = User(name=data.name, email=email, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two sign-ups with the same email at the same moment: the UNIQUE index catches the second.
        db.rollback()
        raise email_taken from None
    db.refresh(user)
    return user


def authenticate(db: Session, data: LoginIn) -> User:
    # Same message for "no such email" and "wrong password", so nobody can probe which emails exist.
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    user = get_user_by_email(db, data.email)
    if user is None or not verify_password(data.password, user.password_hash):
        raise invalid
    return user
