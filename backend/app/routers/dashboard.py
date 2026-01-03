"""Dashboard and summary routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from typing import Optional

from ..database import get_db
from ..models import Account, Transaction, Category
from ..schemas import MonthlySummary, AccountSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_monthly_summary(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get a comprehensive monthly summary."""
    now = datetime.utcnow()
    month = month or now.month
    year = year or now.year
    
    # Get all transactions for the month
    transactions = db.query(Transaction).filter(
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year
    ).all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.is_income)
    total_expenses = sum(t.amount for t in transactions if not t.is_income)
    
    # Spending by category
    category_spending = db.query(
        Category.name,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.is_income == False,
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year
    ).group_by(Category.name).all()
    
    by_category = {name: float(total) for name, total in category_spending}
    
    # Account summaries
    accounts = db.query(Account).filter(Account.is_active == True).all()
    account_summaries = []
    
    for account in accounts:
        spent = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.account_id == account.id,
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
        
        if account.account_type == "credit_card" and account.credit_limit:
            summary["remaining_credit"] = account.credit_limit - float(spent)
            summary["utilization_percent"] = (float(spent) / account.credit_limit) * 100
        
        account_summaries.append(summary)
    
    return {
        "month": month,
        "year": year,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net": total_income - total_expenses,
        "by_category": by_category,
        "by_account": account_summaries
    }


@router.get("/credit-cards")
def get_credit_card_overview(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get an overview of all credit cards with spending and limits."""
    now = datetime.utcnow()
    month = month or now.month
    year = year or now.year
    
    credit_cards = db.query(Account).filter(
        Account.account_type == "credit_card",
        Account.is_active == True
    ).all()
    
    results = []
    for card in credit_cards:
        spent = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.account_id == card.id,
            Transaction.is_income == False,
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar()
        
        results.append({
            "id": card.id,
            "name": card.name,
            "credit_limit": card.credit_limit,
            "spent_this_month": float(spent),
            "remaining_credit": card.credit_limit - float(spent) if card.credit_limit else None,
            "utilization_percent": (float(spent) / card.credit_limit * 100) if card.credit_limit else None
        })
    
    return results


@router.get("/recent-transactions")
def get_recent_transactions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get the most recent transactions."""
    transactions = db.query(Transaction).order_by(
        Transaction.date.desc()
    ).limit(limit).all()
    
    return [{
        "id": t.id,
        "amount": t.amount,
        "description": t.description,
        "date": t.date.isoformat(),
        "is_income": t.is_income,
        "account_id": t.account_id,
        "category_id": t.category_id
    } for t in transactions]
