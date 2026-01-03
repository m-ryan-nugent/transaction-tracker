"""Transaction management routes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Transaction, Account, Category
from ..schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    is_income: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get transactions with optional filters."""
    query = db.query(Transaction).options(
        joinedload(Transaction.account),
        joinedload(Transaction.category)
    )
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if is_income is not None:
        query = query.filter(Transaction.is_income == is_income)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    return query.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """Create a new transaction."""
    # Verify account exists
    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Verify category exists if provided
    if transaction.category_id:
        category = db.query(Category).filter(Category.id == transaction.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    db_transaction = Transaction(**transaction.model_dump())
    db.add(db_transaction)
    
    # Update account balance
    if transaction.is_income:
        account.current_balance += transaction.amount
    else:
        account.current_balance -= transaction.amount
    
    db.commit()
    db.refresh(db_transaction)
    
    # Load relationships for response
    db.refresh(db_transaction, ["account", "category"])
    return db_transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a specific transaction."""
    transaction = db.query(Transaction).options(
        joinedload(Transaction.account),
        joinedload(Transaction.category)
    ).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """Update a transaction."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get the account to update balance
    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    
    # Reverse the old transaction effect on balance
    if transaction.is_income:
        account.current_balance -= transaction.amount
    else:
        account.current_balance += transaction.amount
    
    # Apply updates
    update_data = transaction_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    # Apply new transaction effect on balance
    if transaction.is_income:
        account.current_balance += transaction.amount
    else:
        account.current_balance -= transaction.amount
    
    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Reverse the transaction effect on account balance
    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    if transaction.is_income:
        account.current_balance -= transaction.amount
    else:
        account.current_balance += transaction.amount
    
    db.delete(transaction)
    db.commit()
