"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ============== Account Schemas ==============
class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(..., pattern="^(credit_card|checking|savings|cash)$")
    credit_limit: Optional[float] = None
    current_balance: float = 0.0


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    credit_limit: Optional[float] = None
    current_balance: Optional[float] = None
    is_active: Optional[bool] = None


class AccountResponse(AccountBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Category Schemas ==============
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#6366f1", pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    is_income: bool = False


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# ============== Transaction Schemas ==============
class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=255)
    date: datetime
    account_id: int
    category_id: Optional[int] = None
    is_income: bool = False
    notes: Optional[str] = Field(None, max_length=500)


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    date: Optional[datetime] = None
    category_id: Optional[int] = None
    is_income: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime
    account: Optional[AccountResponse] = None
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


# ============== Budget Schemas ==============
class BudgetItemBase(BaseModel):
    category_id: int
    allocated_amount: float = Field(..., ge=0)


class BudgetItemCreate(BudgetItemBase):
    pass


class BudgetItemResponse(BudgetItemBase):
    id: int
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2100)
    total_budget: float = Field(..., ge=0)


class BudgetCreate(BudgetBase):
    items: List[BudgetItemCreate] = []


class BudgetResponse(BudgetBase):
    id: int
    created_at: datetime
    items: List[BudgetItemResponse] = []

    class Config:
        from_attributes = True


# ============== Subscription Schemas ==============
class SubscriptionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    billing_cycle: str = Field(..., pattern="^(weekly|monthly|yearly)$")
    next_billing_date: datetime
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)
    billing_cycle: Optional[str] = Field(None, pattern="^(weekly|monthly|yearly)$")
    next_billing_date: Optional[datetime] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class SubscriptionResponse(SubscriptionBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Summary/Dashboard Schemas ==============
class AccountSummary(BaseModel):
    account: AccountResponse
    spent_this_month: float
    remaining_credit: Optional[float] = None  # For credit cards
    utilization_percent: Optional[float] = None  # For credit cards


class MonthlySummary(BaseModel):
    month: int
    year: int
    total_income: float
    total_expenses: float
    net: float
    by_category: dict
    by_account: List[AccountSummary]
