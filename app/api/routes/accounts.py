"""Account routes"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_db, get_current_user
from app.api.schemas.account import (
    InvestmentCreate,
    AccountUpdate,
    AccountResponse,
    AccountListResponse,
    AccountSummary,
)
from app.api.services import account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/bank", response_model=AccountResponse, status_code=status.HTTP_201_CREATED
)
async def create_investment(
    account: InvestmentCreate,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Create a new investment account."""
    return await account_service.create_account(db, account)


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """List all accounts with optional filters."""
    return await account_service.get_all_accounts(db, account_type, is_active)


@router.get("/summary", response_model=AccountSummary)
async def get_accounts_summary(
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Get a summary of all accounts (for dashboard)."""
    return await account_service.get_account_summary(db)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Get a specific account by ID."""
    account = await account_service.get_account(db, account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return account


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account: AccountUpdate,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Update an account."""
    existing = await account_service.get_account(db, account_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return await account_service.update_account(db, account_id, account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Delete an account."""
    deleted = await account_service.get_account(db, account_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
