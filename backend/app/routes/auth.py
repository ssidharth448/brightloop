"""Authentication routes — register, login, current user, password reset, staff management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    StaffCreate,
    Token,
    UserLogin,
    UserOut,
    UserRegister,
)
from app.services.auth_service import (
    authenticate_user,
    create_password_reset_token,
    create_token_for_user,
    register_user,
    reset_user_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account."""
    try:
        user = register_user(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and receive a JWT access token."""
    user = authenticate_user(db, data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_token_for_user(user)
    user_out = UserOut.model_validate(user)
    return Token(access_token=token, token=token, user=user_out)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user


# ---------- Staff management (admin only) ----------

@router.post("/staff", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_staff(
    data: StaffCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create a new staff member (admin only)."""
    reg = UserRegister(
        name=data.name,
        email=data.email,
        password=data.password,
        role="staff",
    )
    try:
        user = register_user(db, reg)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    return user


# ---------- Password reset ----------

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset link (simulated — returns token directly)."""
    token_data = create_password_reset_token(db, data.email)
    if token_data is None:
        # Still return success to prevent email enumeration
        return ForgotPasswordResponse(
            message="If the email is registered, a reset link has been sent.",
            reset_token="",
            reset_link="",
        )
    return ForgotPasswordResponse(
        message="Password reset link generated (simulated).",
        reset_token=token_data["token"],
        reset_link=f"/reset-password?token={token_data['token']}",
    )


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset a user password using a valid reset token."""
    success = reset_user_password(db, data.token, data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return {"message": "Password has been reset successfully."}
