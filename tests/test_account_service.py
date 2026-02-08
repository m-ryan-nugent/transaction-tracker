"""Tests for the account service layer."""

import pytest

from app.api.services.account_service import (
    create_account,
    get_account,
    get_all_accounts,
    update_account,
    delete_account,
    get_account_summary,
)
from app.api.schemas.account import (
    BankAccountCreate,
    CreditCardCreate,
    AccountUpdate,
)


@pytest.mark.asyncio
class TestCreateAccount:
    """Tests for account creation."""

    async def test_create_bank_account(self, db_with_user):
        account = await create_account(
            db_with_user,
            BankAccountCreate(
                name="Checking",
                current_balance=2500.0,
                institution="Chase",
            ),
        )
        assert account.name == "Checking"
        assert account.account_type == "bank"
        assert account.current_balance == 2500.0
        assert account.is_active is True

    async def test_create_credit_card(self, db_with_user):
        account = await create_account(
            db_with_user,
            CreditCardCreate(
                name="Visa",
                credit_limit=5000.0,
                current_balance=1200.0,
                interest_rate=19.99,
            ),
        )
        assert account.account_type == "credit_card"
        assert account.credit_limit == 5000.0
        assert account.available_credit == 3800.0


@pytest.mark.asyncio
class TestGetAccount:
    """Tests for fetching accounts."""

    async def test_get_existing_account(self, db_with_account):
        account = await get_account(db_with_account, 1)
        assert account is not None
        assert account.name == "Test Checking"

    async def test_get_nonexistent_account(self, db_with_user):
        account = await get_account(db_with_user, 999)
        assert account is None


@pytest.mark.asyncio
class TestGetAllAccounts:
    """Tests for listing accounts."""

    async def test_get_all_accounts(self, db_with_account):
        result = await get_all_accounts(db_with_account)
        assert result.total >= 1

    async def test_filter_by_type(self, db_with_account):
        result = await get_all_accounts(db_with_account, account_type="credit_card")
        assert result.total == 0

    async def test_filter_by_active(self, db_with_account):
        result = await get_all_accounts(db_with_account, is_active=True)
        assert result.total >= 1


@pytest.mark.asyncio
class TestUpdateAccount:
    """Tests for updating accounts."""

    async def test_update_name(self, db_with_account):
        updated = await update_account(
            db_with_account, 1, AccountUpdate(name="Renamed")
        )
        assert updated.name == "Renamed"

    async def test_update_balance(self, db_with_account):
        updated = await update_account(
            db_with_account, 1, AccountUpdate(current_balance=9999.0)
        )
        assert updated.current_balance == 9999.0

    async def test_update_empty_data(self, db_with_account):
        original = await get_account(db_with_account, 1)
        updated = await update_account(db_with_account, 1, AccountUpdate())
        assert updated.name == original.name


@pytest.mark.asyncio
class TestDeleteAccount:
    """Tests for deleting accounts."""

    async def test_delete_existing(self, db_with_account):
        result = await delete_account(db_with_account, 1)
        assert result is True
        assert await get_account(db_with_account, 1) is None

    async def test_delete_nonexistent(self, db_with_user):
        result = await delete_account(db_with_user, 999)
        assert result is False


@pytest.mark.asyncio
class TestAccountSummary:
    """Tests for account summary."""

    async def test_summary_with_bank_account(self, db_with_account):
        summary = await get_account_summary(db_with_account)
        assert summary.total_assets == 1000.0
        assert summary.total_liabilities == 0.0
        assert summary.net_worth == 1000.0

    async def test_summary_empty(self, db_with_user):
        summary = await get_account_summary(db_with_user)
        assert summary.net_worth == 0.0
