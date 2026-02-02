"""Loan schemas"""

import math
from datetime import date, datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, computed_field


LoanType = Literal["mortgage", "auto", "personal", "student", "other"]


class LoanBase(BaseModel):
    """Base loan fields."""
    name: str = Field(..., min_length=1, max_length=100)
    loan_type: LoanType = "personal"
    original_principal: float = Field(..., gt=0, description="Original loan amount")
    interest_rate: float = Field(..., ge=0, le=100, description="Annual interest rate as percentage")
    term_months: int = Field(..., gt=0, le=600, description="Loan term in months")
    start_date: date
    monthly_payment: Optional[float] = Field(None, ge=0, description="Fixed monthly payment amount")
    account_id: Optional[int] = Field(None, description="Associated account for tracking")
    notes: Optional[str] = Field(None, max_length=500)


class LoanCreate(LoanBase):
    """Schema for creating a new loan."""
    pass


class LoanUpdate(BaseModel):
    """Schema for updating a loan. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    loan_type: Optional[LoanType] = None
    interest_rate: Optional[float] = Field(None, ge=0, le=100)
    monthly_payment: Optional[float] = Field(None, ge=0)
    account_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class LoanResponse(LoanBase):
    """Schema for loan response with computed fields."""
    id: int
    current_balance: float
    total_paid: float
    is_active: bool
    account_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def loan_type_display(self) -> str:
        """Human-readable loan type."""
        types = {
            "mortgage": "Mortgage",
            "auto": "Auto Loan",
            "personal": "Personal Loan",
            "student": "Student Loan",
            "other": "Other",
        }
        return types.get(self.loan_type, self.loan_type)
    
    @computed_field
    @property
    def progress_percent(self) -> float:
        """Percentage of loan paid off."""
        if self.original_principal <= 0:
            return 100.0
        paid = self.original_principal - self.current_balance
        return round((paid / self.original_principal) * 100, 1)
    
    @computed_field
    @property
    def remaining_payments(self) -> int:
        """Estimated remaining payments based on current balance and payment."""
        if not self.monthly_payment or self.monthly_payment <= 0:
            return 0
        if self.current_balance <= 0:
            return 0
        
        monthly_rate = (self.interest_rate / 100) / 12
        if monthly_rate > 0:
            if self.monthly_payment <= self.current_balance * monthly_rate:
                return 999  # Payment doesn't cover interest
            n = -math.log(1 - (self.current_balance * monthly_rate / self.monthly_payment)) / math.log(1 + monthly_rate)
            return max(0, int(math.ceil(n)))
        else:
            return int(math.ceil(self.current_balance / self.monthly_payment))
    
    @computed_field
    @property
    def total_interest_paid(self) -> float:
        """Total interest paid so far."""
        principal_paid = self.original_principal - self.current_balance
        return round(max(0, self.total_paid - principal_paid), 2)

    model_config = {"from_attributes": True}


class LoanListResponse(BaseModel):
    """Response for listing loans."""
    loans: list[LoanResponse]
    total: int
    total_balance: float
    total_original: float


class AmortizationEntry(BaseModel):
    """Single entry in an amortization schedule."""
    payment_number: int
    payment_date: date
    payment_amount: float
    principal: float
    interest: float
    balance: float
    cumulative_interest: float
    cumulative_principal: float


class AmortizationSchedule(BaseModel):
    """Full amortization schedule for a loan."""
    loan_id: int
    loan_name: str
    original_principal: float
    interest_rate: float
    term_months: int
    monthly_payment: float
    total_interest: float
    total_cost: float
    schedule: list[AmortizationEntry]


class LoanPayment(BaseModel):
    """Schema for recording a loan payment."""
    amount: float = Field(..., gt=0)
    payment_date: date
    extra_principal: float = Field(0, ge=0, description="Additional principal payment")
    notes: Optional[str] = Field(None, max_length=500)


class LoanPaymentResponse(BaseModel):
    """Response after recording a payment."""
    id: int
    loan_id: int
    amount: float
    principal_paid: float
    interest_paid: float
    extra_principal: float
    new_balance: float
    payment_date: date
    notes: Optional[str]
    created_at: datetime


class LoanSummary(BaseModel):
    """Summary of all loans for dashboard."""
    total_loans: int
    active_loans: int
    total_balance: float
    total_original: float
    total_monthly_payment: float
    loans_by_type: dict[str, int]
