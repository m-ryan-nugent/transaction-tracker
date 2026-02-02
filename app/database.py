"""Database connection and initialization"""


import aiosqlite

from app.config import DATABASE_PATH


async def get_db() -> aiosqlite.Connection:
    """
    Get a database connection.
    """
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """
    Initialize the database with all required tables.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        
        await _create_users_table(db)
        await _create_accounts_table(db)
        await _create_categories_table(db)
        await _create_transactions_table(db)
        await _create_subscriptions_table(db)
        await _create_loans_table(db)
        await _create_loan_payments_table(db)
        
        await db.commit()


async def _create_users_table(db: aiosqlite.Connection):
    """Create the users table for authentication."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


async def _create_accounts_table(db: aiosqlite.Connection):
    """
    Create the accounts table.
    """
    await db.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL CHECK (account_type IN ('bank', 'credit_card', 'loan', 'investment')),
            
            -- Current balance (updated by transactions or manual edits)
            current_balance REAL NOT NULL DEFAULT 0.0,
            
            -- Credit card specific
            credit_limit REAL,
            
            -- Loan specific
            original_amount REAL,
            interest_rate REAL,
            loan_term_months INTEGER,
            loan_start_date DATE,
            
            -- Investment specific (for tracking purposes)
            initial_investment REAL,
            
            -- Metadata
            institution TEXT,
            notes TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


async def _create_categories_table(db: aiosqlite.Connection):
    """Create the categories table."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense', 'transfer')),
            is_system INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


async def _create_transactions_table(db: aiosqlite.Connection):
    """Create the transactions table."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            payee TEXT,
            notes TEXT,
            
            -- Foreign keys
            account_id INTEGER NOT NULL,
            category_id INTEGER,
            
            -- For transfers between accounts
            transfer_to_account_id INTEGER,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
            FOREIGN KEY (transfer_to_account_id) REFERENCES accounts(id) ON DELETE SET NULL
        )
    """)
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)
    """)
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)
    """)


async def _create_subscriptions_table(db: aiosqlite.Connection):
    """Create the subscriptions table."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            billing_cycle TEXT NOT NULL CHECK (billing_cycle IN ('weekly', 'biweekly', 'monthly', 'quarterly', 'semi_annual', 'annual')),
            next_billing_date DATE NOT NULL,
            
            -- Optional links
            account_id INTEGER,
            category_id INTEGER,
            
            -- Metadata
            notes TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscriptions_next_date ON subscriptions(next_billing_date)
    """)


async def _create_loans_table(db: aiosqlite.Connection):
    """Create the loans table for detailed loan tracking."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            loan_type TEXT NOT NULL CHECK (loan_type IN ('mortgage', 'auto', 'personal', 'student', 'other')),
            original_principal REAL NOT NULL,
            current_balance REAL NOT NULL,
            interest_rate REAL NOT NULL,
            term_months INTEGER NOT NULL,
            start_date DATE NOT NULL,
            monthly_payment REAL,
            total_paid REAL NOT NULL DEFAULT 0.0,
            
            -- Optional link to account
            account_id INTEGER,
            
            -- Metadata
            notes TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
        )
    """)


async def _create_loan_payments_table(db: aiosqlite.Connection):
    """Create the loan_payments table to track individual payments."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS loan_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            principal_paid REAL NOT NULL,
            interest_paid REAL NOT NULL,
            extra_principal REAL NOT NULL DEFAULT 0.0,
            balance_after REAL NOT NULL,
            payment_date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
        )
    """)
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_loan_payments_loan ON loan_payments(loan_id)
    """)
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_loan_payments_date ON loan_payments(payment_date)
    """)


async def seed_categories():
    """
    Seed the database with default categories.
    """
    from app.config import DEFAULT_CATEGORIES
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for category in DEFAULT_CATEGORIES:
            await db.execute("""
                INSERT OR IGNORE INTO categories (name, type, is_system)
                VALUES (?, ?, 1)
            """, (category["name"], category["type"]))
        
        await db.commit()
