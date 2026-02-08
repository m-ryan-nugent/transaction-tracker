"""Loan routes"""

from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_db, get_current_user
from app.api.schemas.loan import (
    LoanCreate,
    LoanUpdate,
    LoanResponse,
    LoanListResponse,
    AmortizationSchedule,
    LoanPayment,
    LoanPaymentResponse,
    LoanSummary,
)
from app.api.services import loan_service

router = APIRouter(
    prefix="/api/loans",
    tags=["loans"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=LoanResponse, status_code=201)
async def create_loan(
    loan: LoanCreate,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Create a new loan."""
    return await loan_service.create_loan(db, loan)


@router.get("", response_model=LoanListResponse)
async def list_loans(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get all loans."""
    return await loan_service.get_all_loans(db, is_active)


@router.get("/summary", response_model=LoanSummary)
async def get_loan_summary(
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get summary of all loans for dashboard."""
    return await loan_service.get_loan_summary(db)


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get a single loan by ID."""
    loan = await loan_service.get_loan_by_id(db, loan_id)
   
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    return loan


@router.get("/{loan_id}/amortization", response_model=AmortizationSchedule)
async def get_amortization_schedule(
    loan_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get the full amortization schedule for a loan."""
    schedule = await loan_service.get_amortization_schedule(db, loan_id)
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    return schedule


@router.get("/{loan_id}/payments", response_model=list[LoanPaymentResponse])
async def get_loan_payments(
    loan_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get payment history for a loan."""
    loan = await loan_service.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    return await loan_service.get_loan_payments(db, loan_id, limit)


@router.post("/{loan_id}/payments", response_model=LoanPaymentResponse, status_code=201)
async def record_payment(
    loan_id: int,
    payment: LoanPayment,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Record a loan payment.
    
    The payment will be split between principal and interest based on
    the current balance and interest rate. Any extra_principal goes
    directly to reducing the loan balance.
    """
    result = await loan_service.record_payment(db, loan_id, payment)
    
    if not result:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    return result


@router.patch("/{loan_id}", response_model=LoanResponse)
async def update_loan(
    loan_id: int,
    update: LoanUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Update a loan."""
    loan = await loan_service.update_loan(db, loan_id, update)
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    return loan