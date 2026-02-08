"""Shared test fixtures and configuration."""

import asyncio
from datetime import date

import aiosqlite
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import init_db, seed_categories
from app.api.services.auth_service import hash_password


TEST_DB = ":memory:"
TEST_USER = {"username": "testuser", "password": "testpassword123"}


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db():
    """Provide a fresh in-memory database for each test."""
    conn = await aiosqlite.connect(TEST_DB)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")

    # Create all tables
    from app.database import (
        _create_users_table,
        _create_accounts_table,
        _create_categories_table,
        _create_transactions_table,
        _create_subscriptions_table,
        _create_loans_table,
        _create_loan_payments_table,
    )
    await _create_users_table(conn)
    await _create_accounts_table(conn)
    await _create_categories_table(conn)
    await _create_transactions_table(conn)
    await _create_subscriptions_table(conn)
    await _create_loans_table(conn)
    await _create_loan_payments_table(conn)
    await conn.commit()

    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def db_with_user(db):
    """Database pre-seeded with a test user."""
    hashed = hash_password(TEST_USER["password"])
    await db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (TEST_USER["username"], hashed),
    )
    await db.commit()
    return db


@pytest_asyncio.fixture
async def db_with_account(db_with_user):
    """Database pre-seeded with a test user and a bank account."""
    await db_with_user.execute(
        "INSERT INTO accounts (name, account_type, current_balance, institution) "
        "VALUES (?, ?, ?, ?)",
        ("Test Checking", "bank", 1000.0, "Test Bank"),
    )
    await db_with_user.commit()
    return db_with_user


@pytest_asyncio.fixture
async def db_with_categories(db_with_account):
    """Database with user, account, and some categories."""
    categories = [
        ("Salary", "income", 1),
        ("Groceries", "expense", 1),
        ("Rent", "expense", 1),
        ("Transfer", "transfer", 1),
    ]
    for name, type_, is_system in categories:
        await db_with_account.execute(
            "INSERT OR IGNORE INTO categories (name, type, is_system) VALUES (?, ?, ?)",
            (name, type_, is_system),
        )
    await db_with_account.commit()
    return db_with_account


@pytest_asyncio.fixture
async def client(db_with_user):
    """Authenticated async HTTP test client using httpx."""
    from app.main import app
    from app.api.dependencies import get_db

    async def override_get_db():
        yield db_with_user

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        # Login to get a token
        login_resp = await ac.post(
            "/api/auth/login",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
        )
        token = login_resp.json()["access_token"]
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauth_client(db_with_user):
    """Unauthenticated async HTTP test client."""
    from app.main import app
    from app.api.dependencies import get_db

    async def override_get_db():
        yield db_with_user

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
