"""Tests for the auth service layer."""

from datetime import timedelta

import pytest

from app.api.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_user,
    get_user_by_username,
    authenticate_user,
    user_exists,
)
from app.api.schemas.auth import UserCreate


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password_returns_string(self):
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert hashed != "mypassword"

    def test_verify_correct_password(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("secret123")
        assert verify_password("wrong", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses random salts


class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_and_decode_token(self):
        token = create_access_token(data={"sub": "alice"})
        token_data = decode_access_token(token)
        assert token_data is not None
        assert token_data.username == "alice"

    def test_decode_invalid_token(self):
        result = decode_access_token("not.a.valid.token")
        assert result is None

    def test_create_token_with_custom_expiry(self):
        token = create_access_token(
            data={"sub": "bob"},
            expires_delta=timedelta(minutes=5),
        )
        token_data = decode_access_token(token)
        assert token_data is not None
        assert token_data.username == "bob"

    def test_token_without_sub_returns_none(self):
        token = create_access_token(data={"other": "value"})
        result = decode_access_token(token)
        assert result is None


@pytest.mark.asyncio
class TestUserDatabase:
    """Tests for user database operations."""

    async def test_create_user(self, db):
        user = await create_user(
            db, UserCreate(username="newuser", password="password123")
        )
        assert user.username == "newuser"
        assert user.id is not None

    async def test_get_user_by_username(self, db_with_user):
        user = await get_user_by_username(db_with_user, "testuser")
        assert user is not None
        assert user["username"] == "testuser"
        assert "password_hash" in user

    async def test_get_nonexistent_user(self, db):
        user = await get_user_by_username(db, "nobody")
        assert user is None

    async def test_authenticate_valid_credentials(self, db_with_user):
        user = await authenticate_user(db_with_user, "testuser", "testpassword123")
        assert user is not None
        assert user["username"] == "testuser"

    async def test_authenticate_wrong_password(self, db_with_user):
        user = await authenticate_user(db_with_user, "testuser", "wrongpassword")
        assert user is None

    async def test_authenticate_nonexistent_user(self, db):
        user = await authenticate_user(db, "ghost", "password")
        assert user is None

    async def test_user_exists_true(self, db_with_user):
        assert await user_exists(db_with_user) is True

    async def test_user_exists_false(self, db):
        assert await user_exists(db) is False
