"""Authentication service — registration, login, token generation."""

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserRegister


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
