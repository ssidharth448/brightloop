"""Tests for user registration, authentication, JWT tokens, and RBAC."""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models
from app.core.database import Base
from app.core.security import decode_access_token
from app.routes.auth import login, me, register
from app.schemas.auth import UserLogin, UserRegister


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_register_user_success(db):
    u = register(
        UserRegister(
            name="Alice Admin",
            email="alice@brightloop.com",
            password="Password123!",
            role="admin",
        ),
        db=db,
    )
    assert u.id == 1
    assert u.email == "alice@brightloop.com"
    assert u.role == "admin"
    assert u.is_active is True


def test_register_duplicate_email(db):
    register(
        UserRegister(
            name="Alice Admin",
            email="alice@brightloop.com",
            password="Password123!",
            role="admin",
        ),
        db=db,
    )
    with pytest.raises(HTTPException) as exc_info:
        register(
            UserRegister(
                name="Alice Two",
                email="alice@brightloop.com",
                password="Password123!",
                role="staff",
            ),
            db=db,
        )
    assert exc_info.value.status_code == 409


def test_login_success(db):
    register(
        UserRegister(
            name="Bob Staff",
            email="bob@brightloop.com",
            password="Password123!",
            role="staff",
        ),
        db=db,
    )
    token = login(
        UserLogin(email="bob@brightloop.com", password="Password123!"),
        db=db,
    )
    assert token.token_type == "bearer"
    payload = decode_access_token(token.access_token)
    assert payload is not None
    assert payload["role"] == "staff"


def test_login_invalid_password(db):
    register(
        UserRegister(
            name="Charlie",
            email="charlie@brightloop.com",
            password="Password123!",
            role="staff",
        ),
        db=db,
    )
    with pytest.raises(HTTPException) as exc_info:
        login(
            UserLogin(email="charlie@brightloop.com", password="WrongPassword"),
            db=db,
        )
    assert exc_info.value.status_code == 401


def test_me_endpoint(db):
    user = register(
        UserRegister(
            name="Dana",
            email="dana@brightloop.com",
            password="Password123!",
            role="admin",
        ),
        db=db,
    )
    res = me(current_user=user)
    assert res.email == "dana@brightloop.com"
    assert res.role == "admin"
