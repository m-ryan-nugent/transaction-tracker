""" "Transaction routes"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.dependencies import get_db, get_current_user
from app.api.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    MonthlySpendingResponse,
)
from app.api.services import transaction_service
from app.api.services import account_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    transaction: TransactionCreate,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Create a new transaction."""
    account = await account_service.get_account(db, transaction.account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Account not found"
        )

    if transaction.transfer_to_account_id:
        dest_account = await account_service.get_account(
            db, transaction.transfer_to_account_id
        )
        if not dest_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer destination account not found",
            )

        if transaction.transfer_to_account_id == transaction.account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer to the same account",
            )

    return await transaction_service.create_transaction(db, transaction)


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """List transactions with optional filters."""
    return await transaction_service.get_transactions(
        db,
        account_id=account_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/recent", response_model=list[TransactionResponse])
async def get_recent_transactions(
    limit: int = Query(default=10, ge=1, le=50),
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Get the most recent transactions."""
    return await transaction_service.get_recent_transactions(db, limit)


@router.get("/monthly-spending", response_model=MonthlySpendingResponse)
async def get_monthly_spending(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Get spending by category for a specific month."""
    return await transaction_service.get_monthly_spending(db, year, month)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Get a specific transaction by ID."""
    transaction = await transaction_service.get_transaction(db, transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Update a transaction."""
    existing = await transaction_service.get_transaction(db, transaction_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    return await transaction_service.update_transaction(db, transaction_id, transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Delete a transaction (also reverses its effect on account balance)."""
    deleted = await transaction_service.delete_transaction(db, transaction_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
