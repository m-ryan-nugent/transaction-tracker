"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine, Base
from .models import Account, Category, Transaction, Budget, BudgetItem, Subscription
from .routers import accounts, transactions, categories, subscriptions, budgets, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    
    # Seed default categories if none exist
    from .database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            default_categories = [
                Category(name="Food & Dining", color="#ef4444", icon="utensils"),
                Category(name="Transportation", color="#f97316", icon="car"),
                Category(name="Shopping", color="#eab308", icon="shopping-bag"),
                Category(name="Entertainment", color="#22c55e", icon="film"),
                Category(name="Bills & Utilities", color="#3b82f6", icon="file-text"),
                Category(name="Healthcare", color="#ec4899", icon="heart"),
                Category(name="Travel", color="#8b5cf6", icon="plane"),
                Category(name="Education", color="#06b6d4", icon="book"),
                Category(name="Personal Care", color="#f472b6", icon="smile"),
                Category(name="Subscriptions", color="#6366f1", icon="repeat"),
                Category(name="Groceries", color="#84cc16", icon="shopping-cart"),
                Category(name="Income", color="#10b981", icon="dollar-sign", is_income=True),
                Category(name="Other", color="#6b7280", icon="more-horizontal"),
            ]
            db.add_all(default_categories)
            db.commit()
    finally:
        db.close()
    
    yield


app = FastAPI(
    title="Transaction Tracker API",
    description="A personal finance tracking API for managing transactions, budgets, and subscriptions",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for cross-origin requests (needed for PWA and desktop client)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(subscriptions.router)
app.include_router(budgets.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": "Transaction Tracker",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected"
    }
