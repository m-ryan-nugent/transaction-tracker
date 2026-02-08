"""Tests for authentication routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import TEST_USER


@pytest.mark.asyncio
class TestAuthSetup:
    """Tests for /api/auth/setup."""

    async def test_setup_creates_user(self, unauth_client):
        """First-time setup should create a user successfully."""
        # The fixture already created a user, so setup should fail
        resp = await unauth_client.post(
            "/api/auth/setup",
            json={"username": "newuser", "password": "newpassword123"},
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]

    async def test_setup_first_user(self, db):
        """When no user exists, setup should succeed."""
        from app.main import app
        from app.api.dependencies import get_db

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            resp = await ac.post(
                "/api/auth/setup",
                json={"username": "firstuser", "password": "securepassword123"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["username"] == "firstuser"
            assert "id" in data

        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestAuthLogin:
    """Tests for /api/auth/login."""

    async def test_login_success(self, unauth_client):
        resp = await unauth_client.post(
            "/api/auth/login",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_sets_cookie(self, unauth_client):
        resp = await unauth_client.post(
            "/api/auth/login",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        )
        assert "access_token" in resp.cookies

    async def test_login_wrong_password(self, unauth_client):
        resp = await unauth_client.post(
            "/api/auth/login",
            data={"username": TEST_USER["username"], "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, unauth_client):
        resp = await unauth_client.post(
            "/api/auth/login",
            data={"username": "nobody", "password": "password123"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestAuthMe:
    """Tests for /api/auth/me."""

    async def test_get_current_user(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == TEST_USER["username"]

    async def test_get_current_user_unauthenticated(self, unauth_client):
        resp = await unauth_client.get("/api/auth/me")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestAuthLogout:
    """Tests for /api/auth/logout."""

    async def test_logout(self, client):
        resp = await client.post("/api/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"


@pytest.mark.asyncio
class TestAuthStatus:
    """Tests for /api/auth/status."""

    async def test_status_when_user_exists(self, unauth_client):
        resp = await unauth_client.get("/api/auth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["setup_required"] is False
