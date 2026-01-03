"""Account management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import Account, Transaction
from ..schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountSummary
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Get all accounts."""
    query = db.query(Account)
    if not include_inactive:
        query = query.filter(Account.is_active == True)
    return query.all()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account."""
    # Validate credit_limit for credit cards
    if account.account_type == "credit_card" and account.credit_limit is None:
        raise HTTPException(
            status_code=400,
            detail="Credit limit is required for credit card accounts"
        )
    
    db_account = Account(**account.model_dump())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get a specific account."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_update: AccountUpdate,
    db: Session = Depends(get_db)
):
    """Update an account."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = account_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Delete an account (soft delete by setting inactive)."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Soft delete
    account.is_active = False
    db.commit()


@router.get("/{account_id}/summary", response_model=AccountSummary)
def get_account_summary(
    account_id: int,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db)
):
    """Get account summary with spending for the current or specified month."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Default to current month/year
    now = datetime.utcnow()
    month = month or now.month
    year = year or now.year
    
    # Calculate spent this month (expenses only)
    spent = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.account_id == account_id,
        Transaction.is_income == False,
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year
    ).scalar()
    
    summary = {
        "account": account,
        "spent_this_month": float(spent),
        "remaining_credit": None,
        "utilization_percent": None
    }
    
    # Calculate credit-specific metrics
    if account.account_type == "credit_card" and account.credit_limit:
        summary["remaining_credit"] = account.credit_limit - float(spent)
        summary["utilization_percent"] = (float(spent) / account.credit_limit) * 100
    
    return summary
