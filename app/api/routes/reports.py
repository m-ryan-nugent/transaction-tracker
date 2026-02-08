"""Report routes"""

from typing import Optional
from datetime import date

import aiosqlite
from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import get_db, get_current_user
from app.api.schemas.report import (
    SpendingByCategory,
    SpendingTrends,
    NetWorthHistory,
)
from app.api.services import report_service

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/spending-by-category", response_model=SpendingByCategory)
async def get_spending_by_category(
    start_date: date = Query(..., description="Start date for the report"),
    end_date: date = Query(..., description="End date for the report"),
    account_id: Optional[int] = Query(None, description="Filter by account"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Get spending breakdown by category for a date range.
    """
    return await report_service.get_spending_by_category(
        db, start_date, end_date, account_id
    )


@router.get("/spending-trends", response_model=SpendingTrends)
async def get_spending_trends(
    months: int = Query(12, ge=1, le=36, description="Number of months to include"),
    account_id: Optional[int] = Query(None, description="Filter by account"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Get monthly income and expense trends.
    """
    return await report_service.get_spending_trends(db, months, account_id)


@router.get("/net-worth", response_model=NetWorthHistory)
async def get_net_worth_history(
    months: int = Query(12, ge=1, le=36, description="Number of months of history"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Get net worth history over time.
    """
    return await report_service.get_net_worth_history(db, months)


@router.get("/export/transactions")
async def export_transactions(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    account_id: Optional[int] = Query(None, description="Filter by account"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Export transactions to CSV file.
    """
    csv_content = await report_service.export_transactions_csv(
        db, start_date, end_date, account_id, category_id
    )
    
    # Generate filename with date range
    if start_date and end_date:
        filename = f"transactions_{start_date}_{end_date}.csv"
    else:
        filename = f"transactions_{date.today()}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/export/accounts")
async def export_accounts(
    db: aiosqlite.Connection = Depends(get_db),
):
    """Export accounts to CSV file."""
    csv_content = await report_service.export_accounts_csv(db)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=accounts_{date.today()}.csv"
        }
    )


@router.get("/export/subscriptions")
async def export_subscriptions(
    db: aiosqlite.Connection = Depends(get_db),
):
    """Export subscriptions to CSV file."""
    csv_content = await report_service.export_subscriptions_csv(db)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=subscriptions_{date.today()}.csv"
        }
    )


@router.get("/export/loans")
async def export_loans(
    db: aiosqlite.Connection = Depends(get_db),
):
    """Export loans to CSV file."""
    csv_content = await report_service.export_loans_csv(db)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=loans_{date.today()}.csv"
        }
    )