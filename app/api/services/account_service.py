"""Account service"""

from typing import Optional
from datetime import datetime

import aiosqlite

from app.api.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountListResponse,
    AccountSummary,
    CreditCardCreate,
    LoanCreate,
    InvestmentCreate,
)


async def create_account(db: aiosqlite.Connection, account: AccountCreate) -> AccountResponse:
    """Create a new account."""
    base_fields = ["name", "account_type", "current_balance", "institution", "notes"]
    base_values = [
        account.name,
        account.account_type,
        account.current_balance,
        account.institution,
        account.notes,
    ]
    
    extra_fields = []
    extra_values = []
    
    if isinstance(account, CreditCardCreate):
        extra_fields = ["credit_limit", "interest_rate"]
        extra_values = [account.credit_limit, account.interest_rate]
    elif isinstance(account, LoanCreate):
        extra_fields = ["original_amount", "interest_rate", "loan_term_months", "loan_start_date"]
        extra_values = [
            account.original_amount,
            account.interest_rate,
            account.loan_term_months,
            account.loan_start_date.isoformat() if account.loan_start_date else None,
        ]
    elif isinstance(account, InvestmentCreate):
        extra_fields = ["initial_investment"]
        extra_values = [account.initial_investment]
    
    all_fields = base_fields + extra_fields
    all_values = base_values + extra_values
    
    placeholders = ", ".join(["?" for _ in all_fields])
    fields_str = ", ".join(all_fields)
    
    cursor = await db.execute(
        f"INSERT INTO accounts ({fields_str}) VALUES ({placeholders})",
        all_values
    )
    await db.commit()
    
    return await get_account(db, cursor.lastrowid)


async def get_account(db: aiosqlite.Connection, account_id: int) -> Optional[AccountResponse]:
    """Get a single account by ID."""
    cursor = await db.execute(
        "SELECT * FROM accounts WHERE id = ?",
        (account_id,)
    )
    row = await cursor.fetchone()
    
    if not row:
        return None
    
    return _row_to_account_response(dict(row))


async def get_all_accounts(
    db: aiosqlite.Connection,
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None
) -> AccountListResponse:
    """Get all accounts with optional filters."""
    query = "SELECT * FROM accounts WHERE 1=1"
    params = []
    
    if account_type:
        query += " AND account_type = ?"
        params.append(account_type)
    
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    query += " ORDER BY name"
    
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    
    accounts = [_row_to_account_response(dict(row)) for row in rows]
    
    return AccountListResponse(accounts=accounts, total=len(accounts))


async def update_account(
    db: aiosqlite.Connection,
    account_id: int,
    account: AccountUpdate
) -> Optional[AccountResponse]:
    """Update an account."""
    update_data = account.model_dump(exclude_unset=True)
    
    if not update_data:
        return await get_account(db, account_id)
    
    if "loan_start_date" in update_data and update_data["loan_start_date"]:
        update_data["loan_start_date"] = update_data["loan_start_date"].isoformat()
    
    if "is_active" in update_data:
        update_data["is_active"] = 1 if update_data["is_active"] else 0
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values()) + [account_id]
    
    await db.execute(
        f"UPDATE accounts SET {set_clause} WHERE id = ?",
        values
    )
    await db.commit()
    
    return await get_account(db, account_id)


async def delete_account(db: aiosqlite.Connection, account_id: int) -> bool:
    """Delete an account."""
    cursor = await db.execute(
        "DELETE FROM accounts WHERE id = ?",
        (account_id,)
    )
    await db.commit()
    
    return cursor.rowcount > 0


async def get_account_summary(db: aiosqlite.Connection) -> AccountSummary:
    """Get a summary of all accounts for the dashboard."""
    accounts_response = await get_all_accounts(db, is_active=True)
    accounts = accounts_response.accounts
    
    total_assets = 0.0
    total_liabilities = 0.0
    accounts_by_type: dict[str, list[AccountResponse]] = {
        "bank": [],
        "credit_card": [],
        "loan": [],
        "investment": [],
    }
    
    for account in accounts:
        accounts_by_type[account.account_type].append(account)
        
        if account.account_type in ("bank", "investment"):
            total_assets += account.current_balance
        else:
            total_liabilities += account.current_balance
    
    return AccountSummary(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=total_assets - total_liabilities,
        accounts_by_type=accounts_by_type,
    )


def _row_to_account_response(row: dict) -> AccountResponse:
    """Convert a database row to an AccountResponse."""
    from datetime import date as date_type
    
    loan_start_date = None
    if row.get("loan_start_date"):
        loan_start_date = date_type.fromisoformat(row["loan_start_date"])
    
    created_at = row.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    updated_at = row.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    available_credit = None
    loan_paid = None
    loan_remaining = None
    
    if row["account_type"] == "credit_card" and row.get("credit_limit"):
        available_credit = row["credit_limit"] - row["current_balance"]
    
    if row["account_type"] == "loan" and row.get("original_amount"):
        loan_paid = row["original_amount"] - row["current_balance"]
        loan_remaining = row["current_balance"]
    
    return AccountResponse(
        id=row["id"],
        name=row["name"],
        account_type=row["account_type"],
        current_balance=row["current_balance"],
        credit_limit=row.get("credit_limit"),
        original_amount=row.get("original_amount"),
        interest_rate=row.get("interest_rate"),
        loan_term_months=row.get("loan_term_months"),
        loan_start_date=loan_start_date,
        initial_investment=row.get("initial_investment"),
        institution=row.get("institution"),
        notes=row.get("notes"),
        is_active=bool(row["is_active"]),
        created_at=created_at or datetime.now(),
        updated_at=updated_at or datetime.now(),
        available_credit=available_credit,
        loan_paid=loan_paid,
        loan_remaining=loan_remaining,
    )
