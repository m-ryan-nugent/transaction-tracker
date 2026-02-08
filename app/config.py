"""Application configuration"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "tracker.db"

DATA_DIR.mkdir(exist_ok=True)

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
TOKEN_ALGORITHM = "HS256"

APP_NAME = "Transaction Tracker"
APP_VERSION = "0.1.0"

DEFAULT_CURRENCY = "USD"

ACCOUNT_TYPES = {
    "bank": {
        "name": "Bank Account",
        "has_credit_limit": False,
        "has_interest_rate": False,
        "has_loan_details": False,
        "balance_increases_on": "income",
    },
    "credit_card": {
        "name": "Credit Card",
        "has_credit_limit": True,
        "has_interest_rate": True,
        "has_loan_details": False,
        "balance_increases_on": "expense",
    },
    "loan": {
        "name": "Loan",
        "has_credit_limit": False,
        "has_interest_rate": True,
        "has_loan_details": True,
        "balance_increases_on": "expense",
    },
    "investment": {
        "name": "Investment",
        "has_credit_limit": False,
        "has_interest_rate": False,
        "has_loan_details": False,
        "balance_increases_on": "income",
    },
}

DEFAULT_CATEGORIES = [
    {"name": "Salary", "type": "income"},
    {"name": "Investment Returns", "type": "income"},
    {"name": "Refund", "type": "income"},
    {"name": "Other Income", "type": "income"},
    {"name": "Housing", "type": "expense"},
    {"name": "Utilities", "type": "expense"},
    {"name": "Groceries", "type": "expense"},
    {"name": "Dining Out", "type": "expense"},
    {"name": "Transportation", "type": "expense"},
    {"name": "Gas", "type": "expense"},
    {"name": "Insurance", "type": "expense"},
    {"name": "Entertainment", "type": "expense"},
    {"name": "Clothing", "type": "expense"},
    {"name": "Subscriptions", "type": "expense"},
    {"name": "Travel", "type": "expense"},
    {"name": "Gifts", "type": "expense"},
    {"name": "Loan Payment", "type": "expense"},
    {"name": "Other Expense", "type": "expense"},
    {"name": "Transfer", "type": "transfer"},
    {"name": "Credit Card Payment", "type": "transfer"},
    {"name": "Investment Contribution", "type": "transfer"},
    {"name": "Investment Withdrawal", "type": "transfer"},
]

BILLING_CYCLES = [
    {"value": "weekly", "name": "Weekly", "days": 7},
    {"value": "biweekly", "name": "Bi-weekly", "days": 14},
    {"value": "monthly", "name": "Monthly", "days": 30},
    {"value": "quarterly", "name": "Quarterly", "days": 90},
    {"value": "semi_annual", "name": "Semi-Annual", "days": 182},
    {"value": "annual", "name": "Annual", "days": 365},
]
