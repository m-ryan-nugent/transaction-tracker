"""Transaction schemas"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    """Base fields for transactions."""
    date: date
    amount: float = Field(..., description="Positive for income, negative for expenses")
    description: Optional[str] = Field(None, max_length=200)
    payee: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    account_id: int
    category_id: Optional[int] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    transfer_to_account_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    date: Optional[date] = None
    amount: Optional[float] = None
    description: Optional[str] = Field(None, max_length=200)
    payee: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    category_id: Optional[int] = None


class TransactionResponse(BaseModel):
    """Schema for transaction responses."""
    id: int
    date: date
    amount: float
    description: Optional[str] = None
    payee: Optional[str] = None
    notes: Optional[str] = None
    account_id: int
    account_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    transfer_to_account_id: Optional[int] = None
    transfer_to_account_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Schema for list of transactions."""
    transactions: list[TransactionResponse]
    total: int


class TransactionFilters(BaseModel):
    """Filters for querying transactions."""
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    search: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class MonthlySpending(BaseModel):
    """Monthly spending by category."""
    month: str
    category_id: int
    category_name: str
    total: float


class MonthlySpendingResponse(BaseModel):
    """Response for monthly spending report."""
    data: list[MonthlySpending]
    total_spent: float
    month: str
