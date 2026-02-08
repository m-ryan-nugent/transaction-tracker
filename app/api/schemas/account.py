"""Account schemas"""

from typing import Optional, Literal
from datetime import date, datetime

from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    """Base fields shared by all account operations."""

    name: str = Field(..., min_length=1, max_length=100)
    account_type: Literal["bank", "credit_card", "loan", "investment"]
    institution: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class BankAccountCreate(AccountBase):
    """Schema for creating a bank account."""

    account_type: Literal["bank"] = "bank"
    current_balance: float = Field(default=0.0, description="Initial balance")


class CreditCardCreate(AccountBase):
    """Schema for creating a credit card account."""

    account_type: Literal["credit_card"] = "credit_card"
    credit_limit: float = Field(..., gt=0, description="Credit limit")
    current_balance: float = Field(default=0.0, ge=0, description="Current amount owed")
    interest_rate: Optional[float] = Field(
        None, ge=0, le=100, description="APR percentage"
    )


class LoanCreate(AccountBase):
    """Schema for creating a loan account."""

    account_type: Literal["loan"] = "loan"
    original_amount: float = Field(..., gt=0, description="Original loan amount")
    current_balance: float = Field(..., ge=0, description="Current amount owed")
    interest_rate: float = Field(
        ..., ge=0, le=100, description="Annual interest rate percentage"
    )
    loan_term_months: int = Field(..., gt=0, description="Loan term in months")
    loan_start_date: date = Field(..., description="Loan start date")


class InvestmentCreate(AccountBase):
    """Schema for creating an investment account."""

    account_type: Literal["investment"] = "investment"
    current_balance: float = Field(default=0.0, description="Current value")
    initial_investment: Optional[float] = Field(
        None, ge=0, description="Initial investment amount"
    )


AccountCreate = BankAccountCreate | CreditCardCreate | LoanCreate | InvestmentCreate


class AccountUpdate(BaseModel):
    """Schema for updating an account. All fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    institution: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    current_balance: Optional[float] = None
    credit_limit: Optional[float] = Field(None, gt=0)
    interest_rate: Optional[float] = Field(None, ge=0, le=100)
    loan_term_months: Optional[int] = Field(None, gt=0)
    loan_start_date: Optional[date] = None
    initial_investment: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    """Schema for account responses."""

    id: int
    name: str
    account_type: str
    current_balance: float
    credit_limit: Optional[float] = None
    original_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    loan_term_months: Optional[int] = None
    loan_start_date: Optional[date] = None
    initial_investment: Optional[float] = None
    institution: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    available_credit: Optional[float] = None
    loan_paid: Optional[float] = None
    loan_remaining: Optional[float] = None

    model_config = {"from_attributes": True}


class AccountListResponse(BaseModel):
    """Schema for list of accounts."""

    accounts: list[AccountResponse]
    total: int


class AccountSummary(BaseModel):
    """Summary of all accounts for dashboard."""

    total_assets: float
    total_liabilities: float
    net_worth: float
    accounts_by_type: dict[str, list[AccountResponse]]
