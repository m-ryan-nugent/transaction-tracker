"""Report schemas"""

from datetime import date
from typing import Optional

from pydantic import BaseModel


class CategorySpending(BaseModel):
    """Spending breakdown for a single category."""

    category_id: Optional[int]
    category_name: str
    total: float
    count: int
    percent: float


class SpendingByCategory(BaseModel):
    """Full spending by category report."""

    start_date: date
    end_date: date
    total_spending: float
    total_income: float
    net: float
    categories: list[CategorySpending]


class MonthlyTrend(BaseModel):
    """Monthly spending/income trend data point."""

    year: int
    month: int
    month_name: str
    income: float
    expenses: float
    net: float


class SpendingTrends(BaseModel):
    """Monthly spending trends over time."""

    months: list[MonthlyTrend]
    average_income: float
    average_expenses: float


class NetWorthDataPoint(BaseModel):
    """Net worth at a point in time."""

    date: date
    assets: float
    liabilities: float
    net_worth: float


class NetWorthHistory(BaseModel):
    """Net worth over time."""

    history: list[NetWorthDataPoint]
    current_net_worth: float
    change_amount: float
    change_percent: float


class ExportRequest(BaseModel):
    """Request parameters for CSV export."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None
