"""Tests for transaction routes."""


import pytest


@pytest.mark.asyncio
class TestCreateTransaction:
    """Tests for POST /api/transactions."""

    async def _create_account(self, client, name="Test Account", balance=1000.0):
        resp = await client.post(
            "/api/accounts/bank",
            json={"name": name, "account_type": "investment", "current_balance": balance},
        )
        return resp.json()["id"]

    async def test_create_transaction(self, client):
        account_id = await self._create_account(client)
        resp = await client.post(
            "/api/transactions",
            json={
                "date": "2026-01-15",
                "amount": -50.0,
                "description": "Groceries",
                "account_id": account_id,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["amount"] == -50.0
        assert data["description"] == "Groceries"
        assert data["account_id"] == account_id

    async def test_create_transaction_invalid_account(self, client):
        resp = await client.post(
            "/api/transactions",
            json={
                "date": "2026-01-15",
                "amount": -10.0,
                "description": "Bad",
                "account_id": 9999,
            },
        )
        assert resp.status_code == 400

    async def test_create_transfer_same_account(self, client):
        account_id = await self._create_account(client)
        resp = await client.post(
            "/api/transactions",
            json={
                "date": "2026-01-15",
                "amount": -100.0,
                "description": "Self transfer",
                "account_id": account_id,
                "transfer_to_account_id": account_id,
            },
        )
        assert resp.status_code == 400
        assert "same account" in resp.json()["detail"]

    async def test_create_transaction_unauthenticated(self, unauth_client):
        resp = await unauth_client.post(
            "/api/transactions",
            json={
                "date": "2026-01-15",
                "amount": -10.0,
                "description": "No auth",
                "account_id": 1,
            },
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestListTransactions:
    """Tests for GET /api/transactions."""

    async def _seed(self, client):
        resp = await client.post(
            "/api/accounts/bank",
            json={"name": "Main", "account_type": "investment", "current_balance": 5000},
        )
        account_id = resp.json()["id"]
        for i in range(3):
            await client.post(
                "/api/transactions",
                json={
                    "date": f"2026-01-{10 + i:02d}",
                    "amount": -(i + 1) * 10.0,
                    "description": f"Purchase {i}",
                    "account_id": account_id,
                },
            )
        return account_id

    async def test_list_transactions(self, client):
        await self._seed(client)
        resp = await client.get("/api/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    async def test_list_transactions_with_account_filter(self, client):
        account_id = await self._seed(client)
        resp = await client.get("/api/transactions", params={"account_id": account_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    async def test_list_transactions_with_date_range(self, client):
        await self._seed(client)
        resp = await client.get(
            "/api/transactions",
            params={"start_date": "2026-01-10", "end_date": "2026-01-11"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestGetTransaction:
    """Tests for GET /api/transactions/{id}."""

    async def test_get_transaction(self, client):
        resp = await client.post(
            "/api/accounts/bank",
            json={"name": "Acc", "account_type": "investment", "current_balance": 1000},
        )
        account_id = resp.json()["id"]
        create_resp = await client.post(
            "/api/transactions",
            json={
                "date": "2026-02-01",
                "amount": -25.0,
                "description": "Coffee",
                "account_id": account_id,
            },
        )
        txn_id = create_resp.json()["id"]

        resp = await client.get(f"/api/transactions/{txn_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == txn_id

    async def test_get_transaction_not_found(self, client):
        resp = await client.get("/api/transactions/9999")
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestRecentTransactions:
    """Tests for GET /api/transactions/recent."""

    async def test_recent_empty(self, client):
        resp = await client.get("/api/transactions/recent")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_recent_returns_limited(self, client):
        resp = await client.post(
            "/api/accounts/bank",
            json={"name": "Acc", "account_type": "investment", "current_balance": 5000},
        )
        account_id = resp.json()["id"]
        for i in range(5):
            await client.post(
                "/api/transactions",
                json={
                    "date": f"2026-01-{i + 1:02d}",
                    "amount": -10.0,
                    "description": f"Txn {i}",
                    "account_id": account_id,
                },
            )
        resp = await client.get("/api/transactions/recent", params={"limit": 3})
        assert resp.status_code == 200
        assert len(resp.json()) == 3
