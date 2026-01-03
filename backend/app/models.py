"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class AccountType(str, enum.Enum):
    """Types of financial accounts."""
    CREDIT_CARD = "credit_card"
    CHECKING = "checking"
    SAVINGS = "savings"
    CASH = "cash"


class Account(Base):
    """Financial account model (credit cards, bank accounts, etc.)."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    account_type = Column(String(20), nullable=False)
    credit_limit = Column(Float, nullable=True)  # Only for credit cards
    current_balance = Column(Float, default=0.0)  # Current balance/amount spent
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    transactions = relationship("Transaction", back_populates="account")


class Category(Base):
    """Transaction category model."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), default="#6366f1")  # Hex color for UI
    icon = Column(String(50), nullable=True)  # Icon name for UI
    is_income = Column(Boolean, default=False)  # True for income categories

    # Relationships
    transactions = relationship("Transaction", back_populates="category")
    budget_items = relationship("BudgetItem", back_populates="category")


class Transaction(Base):
    """Individual transaction model."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_income = Column(Boolean, default=False)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class Budget(Base):
    """Monthly budget model."""
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    total_budget = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    items = relationship("BudgetItem", back_populates="budget")


class BudgetItem(Base):
    """Individual budget category allocation."""
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    allocated_amount = Column(Float, nullable=False)

    # Relationships
    budget = relationship("Budget", back_populates="items")
    category = relationship("Category", back_populates="budget_items")


class Subscription(Base):
    """Recurring subscription model."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    billing_cycle = Column(String(20), nullable=False)  # monthly, yearly, weekly
    next_billing_date = Column(DateTime, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
