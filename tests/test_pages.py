"""Tests for page routes (HTML template responses)."""

import pytest


@pytest.mark.asyncio
class TestPageRoutes:
    """Tests that page routes return HTML responses."""

    async def test_login_page(self, unauth_client):
        resp = await unauth_client.get("/login")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    async def test_setup_page(self, unauth_client):
        resp = await unauth_client.get("/setup")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    async def test_dashboard_page(self, unauth_client):
        resp = await unauth_client.get("/dashboard")
        assert resp.status_code == 200

    async def test_accounts_page(self, unauth_client):
        resp = await unauth_client.get("/accounts")
        assert resp.status_code == 200

    async def test_transactions_page(self, unauth_client):
        resp = await unauth_client.get("/transactions")
        assert resp.status_code == 200

    async def test_subscriptions_page(self, unauth_client):
        resp = await unauth_client.get("/subscriptions")
        assert resp.status_code == 200

    async def test_loans_page(self, unauth_client):
        resp = await unauth_client.get("/loans")
        assert resp.status_code == 200

    async def test_reports_page(self, unauth_client):
        resp = await unauth_client.get("/reports")
        assert resp.status_code == 200

    async def test_home_redirects_to_login(self, unauth_client):
        resp = await unauth_client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers.get("location", "") or "/setup" in resp.headers.get("location", "")
