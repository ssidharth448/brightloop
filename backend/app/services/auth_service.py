"""Authentication service — registration, login, token generation, and password reset."""

import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserRegister

# In-memory store for password reset tokens: token -> {user_id, expires_at}
_RESET_TOKENS: dict[str, dict] = {}


def register_user(db: Session, data: UserRegister) -> User:
    """Create a new user with a hashed password."""
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user if credentials are valid, else None."""
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_token_for_user(user: User) -> str:
    """Generate a JWT access token for the given user."""
    return create_access_token(data={"sub": str(user.id), "role": user.role})


def create_password_reset_token(db: Session, email: str) -> str:
    """Create and record a password reset token for the specified email."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User with this email not found")

    token = secrets.token_urlsafe(32)
    _RESET_TOKENS[token] = {
        "user_id": user.id,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return token


def reset_user_password(db: Session, token: str, new_password: str) -> User:
    """Reset the user password if the reset token is valid and unexpired."""
    record = _RESET_TOKENS.get(token)
    if not record:
        raise ValueError("Invalid or expired password reset token")

    if datetime.now(timezone.utc) > record["expires_at"]:
        _RESET_TOKENS.pop(token, None)
        raise ValueError("Password reset token has expired")

    user = db.get(User, record["user_id"])
    if not user:
        raise ValueError("User not found")

    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    _RESET_TOKENS.pop(token, None)
    return user
