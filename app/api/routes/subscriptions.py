""" "Subscription routes"""

from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_db, get_current_user
from app.api.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionListResponse,
    UpcomingRenewal,
)
from app.api.services import subscription_service

router = APIRouter(
    prefix="/api/subscriptions",
    tags=["subscriptions"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    subscription: SubscriptionCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Create a new subscription."""
    return await subscription_service.create_subscription(db, subscription)


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Get all subscriptions.
    """
    return await subscription_service.get_all_subscriptions(db, is_active)


@router.get("/upcoming", response_model=list[UpcomingRenewal])
async def get_upcoming_renewals(
    days: int = Query(30, ge=1, le=365, description="Number of days to look ahead"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get upcoming subscription renewals."""
    return await subscription_service.get_upcoming_renewals(db, days, limit)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get a single subscription by ID."""
    subscription = await subscription_service.get_subscription(db, subscription_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return subscription


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update: SubscriptionUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Update a subscription."""
    subscription = await subscription_service.update_subscription(
        db, subscription_id, update
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return subscription


@router.delete("/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Delete a subscription."""
    deleted = await subscription_service.delete_subscription(db, subscription_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Subscription not found")


@router.post("/{subscription_id}/advance", response_model=SubscriptionResponse)
async def advance_billing_date(
    subscription_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Advance a subscription's billing date to the next cycle.
    """
    subscription = await subscription_service.advance_billing_date(db, subscription_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return subscription
