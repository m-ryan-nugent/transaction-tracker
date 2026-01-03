"""Subscription management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Subscription, Account, Category
from ..schemas import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/", response_model=List[SubscriptionResponse])
def get_subscriptions(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Get all subscriptions."""
    query = db.query(Subscription)
    if not include_inactive:
        query = query.filter(Subscription.is_active == True)
    return query.order_by(Subscription.next_billing_date).all()


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(subscription: SubscriptionCreate, db: Session = Depends(get_db)):
    """Create a new subscription."""
    # Verify account exists if provided
    if subscription.account_id:
        account = db.query(Account).filter(Account.id == subscription.account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
    
    # Verify category exists if provided
    if subscription.category_id:
        category = db.query(Category).filter(Category.id == subscription.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    db_subscription = Subscription(**subscription.model_dump())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


@router.get("/upcoming", response_model=List[SubscriptionResponse])
def get_upcoming_subscriptions(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get subscriptions due within the specified number of days."""
    cutoff_date = datetime.utcnow() + timedelta(days=days)
    return db.query(Subscription).filter(
        Subscription.is_active == True,
        Subscription.next_billing_date <= cutoff_date
    ).order_by(Subscription.next_billing_date).all()


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Get a specific subscription."""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    subscription_update: SubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """Update a subscription."""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    update_data = subscription_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)
    
    db.commit()
    db.refresh(subscription)
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Delete a subscription."""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    db.delete(subscription)
    db.commit()


@router.post("/{subscription_id}/mark-paid", response_model=SubscriptionResponse)
def mark_subscription_paid(subscription_id: int, db: Session = Depends(get_db)):
    """Mark a subscription as paid and update the next billing date."""
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Calculate next billing date based on cycle
    current_date = subscription.next_billing_date
    if subscription.billing_cycle == "weekly":
        subscription.next_billing_date = current_date + timedelta(weeks=1)
    elif subscription.billing_cycle == "monthly":
        # Add one month
        month = current_date.month + 1
        year = current_date.year
        if month > 12:
            month = 1
            year += 1
        # Handle end-of-month edge cases
        day = min(current_date.day, 28)  # Safe day for all months
        subscription.next_billing_date = current_date.replace(year=year, month=month, day=day)
    elif subscription.billing_cycle == "yearly":
        subscription.next_billing_date = current_date.replace(year=current_date.year + 1)
    
    db.commit()
    db.refresh(subscription)
    return subscription
