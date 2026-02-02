"""Transaction service"""

from typing import Optional
from datetime import datetime, date

import aiosqlite

from app.api.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    MonthlySpending,
    MonthlySpendingResponse,
)


async def create_transaction(
    db: aiosqlite.Connection,
    transaction: TransactionCreate
) -> TransactionResponse:
    """
    Create a new transaction and update account balance(s).
    """
    cursor = await db.execute(
        """
        INSERT INTO transactions (
            date, amount, description, payee, notes,
            account_id, category_id, transfer_to_account_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction.date.isoformat(),
            transaction.amount,
            transaction.description,
            transaction.payee,
            transaction.notes,
            transaction.account_id,
            transaction.category_id,
            transaction.transfer_to_account_id,
        )
    )
    transaction_id = cursor.lastrowid
    
    await _update_account_balance(db, transaction.account_id, transaction.amount)
    
    if transaction.transfer_to_account_id:
        await _update_account_balance(
            db, 
            transaction.transfer_to_account_id, 
            -transaction.amount
        )
    
    await db.commit()
    
    return await get_transaction(db, transaction_id)


async def get_transaction(
    db: aiosqlite.Connection,
    transaction_id: int
) -> Optional[TransactionResponse]:
    """Get a single transaction by ID with related data."""
    cursor = await db.execute(
        """
        SELECT 
            t.*,
            a.name as account_name,
            c.name as category_name,
            ta.name as transfer_to_account_name
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts ta ON t.transfer_to_account_id = ta.id
        WHERE t.id = ?
        """,
        (transaction_id,)
    )
    row = await cursor.fetchone()
    
    if not row:
        return None
    
    return _row_to_transaction_response(dict(row))


async def get_transactions(
    db: aiosqlite.Connection,
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> TransactionListResponse:
    """Get transactions with filters."""
    query = """
        SELECT 
            t.*,
            a.name as account_name,
            c.name as category_name,
            ta.name as transfer_to_account_name
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts ta ON t.transfer_to_account_id = ta.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as total FROM transactions t WHERE 1=1"
    params = []
    count_params = []
    
    if account_id:
        condition = " AND (t.account_id = ? OR t.transfer_to_account_id = ?)"
        query += condition
        count_query += condition
        params.extend([account_id, account_id])
        count_params.extend([account_id, account_id])
    
    if category_id:
        condition = " AND t.category_id = ?"
        query += condition
        count_query += condition
        params.append(category_id)
        count_params.append(category_id)
    
    if start_date:
        condition = " AND t.date >= ?"
        query += condition
        count_query += condition
        params.append(start_date.isoformat())
        count_params.append(start_date.isoformat())
    
    if end_date:
        condition = " AND t.date <= ?"
        query += condition
        count_query += condition
        params.append(end_date.isoformat())
        count_params.append(end_date.isoformat())
    
    if min_amount is not None:
        condition = " AND ABS(t.amount) >= ?"
        query += condition
        count_query += condition
        params.append(abs(min_amount))
        count_params.append(abs(min_amount))
    
    if max_amount is not None:
        condition = " AND ABS(t.amount) <= ?"
        query += condition
        count_query += condition
        params.append(abs(max_amount))
        count_params.append(abs(max_amount))
    
    if search:
        condition = " AND (t.description LIKE ? OR t.payee LIKE ? OR t.notes LIKE ?)"
        search_term = f"%{search}%"
        query += condition
        count_query += condition
        params.extend([search_term, search_term, search_term])
        count_params.extend([search_term, search_term, search_term])
    
    # Get total count
    cursor = await db.execute(count_query, count_params)
    total_row = await cursor.fetchone()
    total = total_row["total"]
    
    # Get transactions with pagination
    query += " ORDER BY t.date DESC, t.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    
    transactions = [_row_to_transaction_response(dict(row)) for row in rows]
    
    return TransactionListResponse(transactions=transactions, total=total)


async def get_recent_transactions(
    db: aiosqlite.Connection,
    limit: int = 10
) -> list[TransactionResponse]:
    """Get the most recent transactions."""
    result = await get_transactions(db, limit=limit)
    return result.transactions


async def update_transaction(
    db: aiosqlite.Connection,
    transaction_id: int,
    update: TransactionUpdate
) -> Optional[TransactionResponse]:
    """Update a transaction and adjust account balance if amount changed."""
    existing = await get_transaction(db, transaction_id)
    if not existing:
        return None
    
    update_data = update.model_dump(exclude_unset=True)
    
    if not update_data:
        return existing
    
    if "date" in update_data and update_data["date"]:
        update_data["date"] = update_data["date"].isoformat()
    
    if "amount" in update_data:
        old_amount = existing.amount
        new_amount = update_data["amount"]
        difference = new_amount - old_amount
        
        if difference != 0:
            await _update_account_balance(db, existing.account_id, difference)
            
            if existing.transfer_to_account_id:
                await _update_account_balance(
                    db, 
                    existing.transfer_to_account_id, 
                    -difference
                )
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values()) + [transaction_id]
    
    await db.execute(
        f"UPDATE transactions SET {set_clause} WHERE id = ?",
        values
    )
    await db.commit()
    
    return await get_transaction(db, transaction_id)


async def delete_transaction(db: aiosqlite.Connection, transaction_id: int) -> bool:
    """Delete a transaction and reverse its effect on account balance."""
    existing = await get_transaction(db, transaction_id)
    if not existing:
        return False
    
    await _update_account_balance(db, existing.account_id, -existing.amount)
    
    if existing.transfer_to_account_id:
        await _update_account_balance(
            db, 
            existing.transfer_to_account_id, 
            existing.amount
        )
    
    cursor = await db.execute(
        "DELETE FROM transactions WHERE id = ?",
        (transaction_id,)
    )
    await db.commit()
    
    return cursor.rowcount > 0


async def get_monthly_spending(
    db: aiosqlite.Connection,
    year: int,
    month: int
) -> MonthlySpendingResponse:
    """Get spending by category for a specific month."""
    month_str = f"{year}-{month:02d}"
    start_date = f"{month_str}-01"
    
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    cursor = await db.execute(
        """
        SELECT 
            c.id as category_id,
            c.name as category_name,
            SUM(ABS(t.amount)) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.date >= ? AND t.date < ?
            AND t.amount < 0  -- Only expenses
            AND c.type = 'expense'
        GROUP BY c.id, c.name
        ORDER BY total DESC
        """,
        (start_date, end_date)
    )
    
    rows = await cursor.fetchall()
    
    data = []
    total_spent = 0.0
    
    for row in rows:
        row_dict = dict(row)
        total = row_dict["total"] or 0
        data.append(MonthlySpending(
            month=month_str,
            category_id=row_dict["category_id"],
            category_name=row_dict["category_name"],
            total=total,
        ))
        total_spent += total
    
    return MonthlySpendingResponse(
        data=data,
        total_spent=total_spent,
        month=month_str,
    )


async def _update_account_balance(
    db: aiosqlite.Connection,
    account_id: int,
    amount: float
) -> None:
    """
    Update an account's balance by the given amount.
    """
    await db.execute(
        """
        UPDATE accounts 
        SET current_balance = current_balance + ?,
            updated_at = ?
        WHERE id = ?
        """,
        (amount, datetime.now().isoformat(), account_id)
    )


def _row_to_transaction_response(row: dict) -> TransactionResponse:
    """Convert a database row to a TransactionResponse."""
    date_val = row.get("date")
    if isinstance(date_val, str):
        date_val = date.fromisoformat(date_val)
    
    created_at = row.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    updated_at = row.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    return TransactionResponse(
        id=row["id"],
        date=date_val,
        amount=row["amount"],
        description=row.get("description"),
        payee=row.get("payee"),
        notes=row.get("notes"),
        account_id=row["account_id"],
        account_name=row.get("account_name"),
        category_id=row.get("category_id"),
        category_name=row.get("category_name"),
        transfer_to_account_id=row.get("transfer_to_account_id"),
        transfer_to_account_name=row.get("transfer_to_account_name"),
        created_at=created_at or datetime.now(),
        updated_at=updated_at or datetime.now(),
    )
