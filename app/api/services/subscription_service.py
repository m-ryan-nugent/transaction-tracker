"""Subscription service"""

from typing import Optional
from datetime import datetime, date, timedelta

import aiosqlite

from app.api.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionListResponse,
    UpcomingRenewal,
)
from app.config import BILLING_CYCLES


CYCLE_INFO = {cycle["value"]: cycle for cycle in BILLING_CYCLES}


def get_cycle_days(billing_cycle: str) -> int:
    """Get the number of days in a billing cycle."""
    return CYCLE_INFO.get(billing_cycle, {}).get("days", 30)


def get_cycle_display(billing_cycle: str) -> str:
    """Get the human-readable name for a billing cycle."""
    return CYCLE_INFO.get(billing_cycle, {}).get("name", billing_cycle)


def calculate_yearly_cost(amount: float, billing_cycle: str) -> float:
    """Calculate the annualized cost of a subscription."""
    days = get_cycle_days(billing_cycle)
    return (365 / days) * amount


def calculate_monthly_cost(amount: float, billing_cycle: str) -> float:
    """Calculate the monthly cost of a subscription."""
    days = get_cycle_days(billing_cycle)
    return (30 / days) * amount


async def create_subscription(
    db: aiosqlite.Connection,
    subscription: SubscriptionCreate
) -> SubscriptionResponse:
    """Create a new subscription."""
    cursor = await db.execute(
        """
        INSERT INTO subscriptions (
            name, amount, billing_cycle, next_billing_date,
            account_id, category_id, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subscription.name,
            subscription.amount,
            subscription.billing_cycle,
            subscription.next_billing_date.isoformat(),
            subscription.account_id,
            subscription.category_id,
            subscription.notes,
        )
    )
    await db.commit()
    
    return await get_subscription(db, cursor.lastrowid)


async def get_subscription(
    db: aiosqlite.Connection,
    subscription_id: int
) -> Optional[SubscriptionResponse]:
    """Get a single subscription by ID with related data."""
    cursor = await db.execute(
        """
        SELECT 
            s.*,
            a.name as account_name,
            c.name as category_name
        FROM subscriptions s
        LEFT JOIN accounts a ON s.account_id = a.id
        LEFT JOIN categories c ON s.category_id = c.id
        WHERE s.id = ?
        """,
        (subscription_id,)
    )
    row = await cursor.fetchone()
    
    if not row:
        return None
    
    return _row_to_subscription_response(dict(row))


async def get_all_subscriptions(
    db: aiosqlite.Connection,
    is_active: Optional[bool] = None
) -> SubscriptionListResponse:
    """Get all subscriptions with optional active filter."""
    query = """
        SELECT 
            s.*,
            a.name as account_name,
            c.name as category_name
        FROM subscriptions s
        LEFT JOIN accounts a ON s.account_id = a.id
        LEFT JOIN categories c ON s.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if is_active is not None:
        query += " AND s.is_active = ?"
        params.append(1 if is_active else 0)
    
    query += " ORDER BY s.next_billing_date ASC"
    
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    
    subscriptions = [_row_to_subscription_response(dict(row)) for row in rows]
    
    active_subs = [s for s in subscriptions if s.is_active]
    total_monthly = sum(calculate_monthly_cost(s.amount, s.billing_cycle) for s in active_subs)
    total_yearly = sum(s.yearly_cost for s in active_subs)
    
    return SubscriptionListResponse(
        subscriptions=subscriptions,
        total=len(subscriptions),
        total_monthly_cost=round(total_monthly, 2),
        total_yearly_cost=round(total_yearly, 2),
    )


async def get_upcoming_renewals(
    db: aiosqlite.Connection,
    days_ahead: int = 30,
    limit: int = 10
) -> list[UpcomingRenewal]:
    """Get upcoming subscription renewals within the specified days."""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    
    cursor = await db.execute(
        """
        SELECT 
            s.id, s.name, s.amount, s.next_billing_date,
            a.name as account_name
        FROM subscriptions s
        LEFT JOIN accounts a ON s.account_id = a.id
        WHERE s.is_active = 1
            AND s.next_billing_date >= ?
            AND s.next_billing_date <= ?
        ORDER BY s.next_billing_date ASC
        LIMIT ?
        """,
        (today.isoformat(), end_date.isoformat(), limit)
    )
    rows = await cursor.fetchall()
    
    renewals = []
    for row in rows:
        row_dict = dict(row)
        next_date = date.fromisoformat(row_dict["next_billing_date"])
        days_until = (next_date - today).days
        
        renewals.append(UpcomingRenewal(
            id=row_dict["id"],
            name=row_dict["name"],
            amount=row_dict["amount"],
            next_billing_date=next_date,
            days_until_renewal=days_until,
            account_name=row_dict.get("account_name"),
        ))
    
    return renewals


async def update_subscription(
    db: aiosqlite.Connection,
    subscription_id: int,
    update: SubscriptionUpdate
) -> Optional[SubscriptionResponse]:
    """Update a subscription."""
    update_data = update.model_dump(exclude_unset=True)
    
    if not update_data:
        return await get_subscription(db, subscription_id)
    
    if "next_billing_date" in update_data and update_data["next_billing_date"]:
        update_data["next_billing_date"] = update_data["next_billing_date"].isoformat()
    
    if "is_active" in update_data:
        update_data["is_active"] = 1 if update_data["is_active"] else 0
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values()) + [subscription_id]
    
    await db.execute(
        f"UPDATE subscriptions SET {set_clause} WHERE id = ?",
        values
    )
    await db.commit()
    
    return await get_subscription(db, subscription_id)


async def delete_subscription(db: aiosqlite.Connection, subscription_id: int) -> bool:
    """Delete a subscription."""
    cursor = await db.execute(
        "DELETE FROM subscriptions WHERE id = ?",
        (subscription_id,)
    )
    await db.commit()
    
    return cursor.rowcount > 0


async def advance_billing_date(
    db: aiosqlite.Connection,
    subscription_id: int
) -> Optional[SubscriptionResponse]:
    """
    Advance a subscription's billing date to the next cycle.
    Call this after a subscription payment is recorded.
    """
    subscription = await get_subscription(db, subscription_id)
    if not subscription:
        return None
    
    days = get_cycle_days(subscription.billing_cycle)
    current_date = subscription.next_billing_date
    next_date = current_date + timedelta(days=days)
    
    await db.execute(
        """
        UPDATE subscriptions 
        SET next_billing_date = ?, updated_at = ?
        WHERE id = ?
        """,
        (next_date.isoformat(), datetime.now().isoformat(), subscription_id)
    )
    await db.commit()
    
    return await get_subscription(db, subscription_id)


def _row_to_subscription_response(row: dict) -> SubscriptionResponse:
    """Convert a database row to a SubscriptionResponse."""
    next_billing_date = row.get("next_billing_date")
    if isinstance(next_billing_date, str):
        next_billing_date = date.fromisoformat(next_billing_date)
    
    created_at = row.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    updated_at = row.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    today = date.today()
    days_until = (next_billing_date - today).days if next_billing_date else 0
    
    billing_cycle = row["billing_cycle"]
    yearly_cost = calculate_yearly_cost(row["amount"], billing_cycle)
    
    return SubscriptionResponse(
        id=row["id"],
        name=row["name"],
        amount=row["amount"],
        billing_cycle=billing_cycle,
        billing_cycle_display=get_cycle_display(billing_cycle),
        next_billing_date=next_billing_date,
        days_until_renewal=days_until,
        account_id=row.get("account_id"),
        account_name=row.get("account_name"),
        category_id=row.get("category_id"),
        category_name=row.get("category_name"),
        notes=row.get("notes"),
        is_active=bool(row["is_active"]),
        yearly_cost=round(yearly_cost, 2),
        created_at=created_at or datetime.now(),
        updated_at=updated_at or datetime.now(),
    )
