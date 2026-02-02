"""Subscription schemas"""

from datetime import date, datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


BillingCycle = Literal["weekly", "biweekly", "monthly", "quarterly", "semi_annual", "annual"]


class SubscriptionBase(BaseModel):
    """Base fields for subscriptions."""
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0, description="Subscription cost per billing cycle")
    billing_cycle: BillingCycle
    next_billing_date: date


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription."""
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    notes: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)
    billing_cycle: Optional[BillingCycle] = None
    next_billing_date: Optional[date] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SubscriptionResponse(BaseModel):
    """Schema for subscription responses."""
    id: int
    name: str
    amount: float
    billing_cycle: str
    billing_cycle_display: str
    next_billing_date: date
    days_until_renewal: int 
    account_id: Optional[int] = None
    account_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    yearly_cost: float
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class SubscriptionListResponse(BaseModel):
    """Schema for list of subscriptions."""
    subscriptions: list[SubscriptionResponse]
    total: int
    total_monthly_cost: float
    total_yearly_cost: float


class UpcomingRenewal(BaseModel):
    """Schema for upcoming subscription renewals."""
    id: int
    name: str
    amount: float
    next_billing_date: date
    days_until_renewal: int
    account_name: Optional[str] = None
