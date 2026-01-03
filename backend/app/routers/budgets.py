"""Budget management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Budget, BudgetItem, Category, Transaction
from ..schemas import BudgetCreate, BudgetResponse

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all budgets, optionally filtered by year."""
    query = db.query(Budget).options(
        joinedload(Budget.items).joinedload(BudgetItem.category)
    )
    if year:
        query = query.filter(Budget.year == year)
    return query.order_by(Budget.year.desc(), Budget.month.desc()).all()


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    """Create a new budget for a month."""
    # Check if budget for this month/year already exists
    existing = db.query(Budget).filter(
        Budget.month == budget.month,
        Budget.year == budget.year
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Budget for {budget.month}/{budget.year} already exists"
        )
    
    # Create budget
    db_budget = Budget(
        month=budget.month,
        year=budget.year,
        total_budget=budget.total_budget
    )
    db.add(db_budget)
    db.flush()  # Get the budget ID
    
    # Create budget items
    for item in budget.items:
        # Verify category exists
        category = db.query(Category).filter(Category.id == item.category_id).first()
        if not category:
            raise HTTPException(
                status_code=404,
                detail=f"Category {item.category_id} not found"
            )
        
        db_item = BudgetItem(
            budget_id=db_budget.id,
            category_id=item.category_id,
            allocated_amount=item.allocated_amount
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_budget)
    return db_budget


@router.get("/current", response_model=BudgetResponse)
def get_current_budget(db: Session = Depends(get_db)):
    """Get the budget for the current month."""
    now = datetime.utcnow()
    budget = db.query(Budget).options(
        joinedload(Budget.items).joinedload(BudgetItem.category)
    ).filter(
        Budget.month == now.month,
        Budget.year == now.year
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=404,
            detail=f"No budget found for {now.month}/{now.year}"
        )
    return budget


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(budget_id: int, db: Session = Depends(get_db)):
    """Get a specific budget."""
    budget = db.query(Budget).options(
        joinedload(Budget.items).joinedload(BudgetItem.category)
    ).filter(Budget.id == budget_id).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.get("/{budget_id}/progress")
def get_budget_progress(budget_id: int, db: Session = Depends(get_db)):
    """Get budget progress with actual spending per category."""
    budget = db.query(Budget).options(
        joinedload(Budget.items).joinedload(BudgetItem.category)
    ).filter(Budget.id == budget_id).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Get actual spending by category for this month
    spending = db.query(
        Transaction.category_id,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.is_income == False,
        extract('month', Transaction.date) == budget.month,
        extract('year', Transaction.date) == budget.year
    ).group_by(Transaction.category_id).all()
    
    spending_map = {s[0]: float(s[1]) for s in spending}
    
    # Build progress report
    items_progress = []
    total_allocated = 0
    total_spent = 0
    
    for item in budget.items:
        spent = spending_map.get(item.category_id, 0)
        total_allocated += item.allocated_amount
        total_spent += spent
        
        items_progress.append({
            "category": item.category.name if item.category else "Unknown",
            "category_id": item.category_id,
            "allocated": item.allocated_amount,
            "spent": spent,
            "remaining": item.allocated_amount - spent,
            "percent_used": (spent / item.allocated_amount * 100) if item.allocated_amount > 0 else 0
        })
    
    return {
        "budget_id": budget.id,
        "month": budget.month,
        "year": budget.year,
        "total_budget": budget.total_budget,
        "total_allocated": total_allocated,
        "total_spent": total_spent,
        "total_remaining": budget.total_budget - total_spent,
        "percent_used": (total_spent / budget.total_budget * 100) if budget.total_budget > 0 else 0,
        "items": items_progress
    }


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """Delete a budget and its items."""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Delete associated items first
    db.query(BudgetItem).filter(BudgetItem.budget_id == budget_id).delete()
    db.delete(budget)
    db.commit()
