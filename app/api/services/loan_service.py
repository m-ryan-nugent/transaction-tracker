"""Loan service"""

import math
from typing import Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

import aiosqlite

from app.api.schemas.loan import (
    LoanCreate,
    LoanUpdate,
    LoanResponse,
    LoanListResponse,
    AmortizationEntry,
    AmortizationSchedule,
    LoanPayment,
    LoanPaymentResponse,
    LoanSummary,
)


def calculate_monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    """
    Calculate the monthly payment for a loan using the amortization formula.
    
    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate as a percentage (e.g., 5.0 for 5%)
        term_months: Loan term in months
    
    Returns:
        Monthly payment amount
    """
    if annual_rate <= 0:
        return principal / term_months
    
    monthly_rate = (annual_rate / 100) / 12
    
    numerator = monthly_rate * math.pow(1 + monthly_rate, term_months)
    denominator = math.pow(1 + monthly_rate, term_months) - 1
    
    return principal * (numerator / denominator)


def generate_amortization_schedule(
    principal: float,
    annual_rate: float,
    term_months: int,
    start_date: date,
    monthly_payment: Optional[float] = None
) -> list[AmortizationEntry]:
    """
    Generate a full amortization schedule for a loan.
    
    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate as percentage
        term_months: Loan term in months
        start_date: Loan start date
        monthly_payment: Optional fixed payment (calculated if not provided)
    
    Returns:
        List of AmortizationEntry objects
    """
    if monthly_payment is None:
        monthly_payment = calculate_monthly_payment(principal, annual_rate, term_months)
    
    monthly_rate = (annual_rate / 100) / 12
    balance = principal
    schedule = []
    cumulative_interest = 0
    cumulative_principal = 0
    
    for month in range(1, term_months + 1):
        payment_date = start_date + relativedelta(months=month)
        
        interest = balance * monthly_rate
        
        principal_payment = min(monthly_payment - interest, balance)
        
        if principal_payment < 0:
            principal_payment = 0
        
        if month == term_months or balance - principal_payment < 0.01:
            principal_payment = balance
            payment_amount = principal_payment + interest
        else:
            payment_amount = monthly_payment
        
        balance = max(0, balance - principal_payment)
        
        cumulative_interest += interest
        cumulative_principal += principal_payment
        
        schedule.append(AmortizationEntry(
            payment_number=month,
            payment_date=payment_date,
            payment_amount=round(payment_amount, 2),
            principal=round(principal_payment, 2),
            interest=round(interest, 2),
            balance=round(balance, 2),
            cumulative_interest=round(cumulative_interest, 2),
            cumulative_principal=round(cumulative_principal, 2),
        ))
        
        if balance <= 0:
            break
    
    return schedule


async def create_loan(db: aiosqlite.Connection, loan: LoanCreate) -> LoanResponse:
    """Create a new loan."""
    # Calculate monthly payment if not provided
    monthly_payment = loan.monthly_payment
    if monthly_payment is None:
        monthly_payment = calculate_monthly_payment(
            loan.original_principal,
            loan.interest_rate,
            loan.term_months
        )
    
    cursor = await db.execute(
        """
        INSERT INTO loans (
            name, loan_type, original_principal, current_balance,
            interest_rate, term_months, start_date, monthly_payment,
            account_id, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            loan.name,
            loan.loan_type,
            loan.original_principal,
            loan.original_principal,
            loan.term_months,
            loan.start_date.isoformat(),
            round(monthly_payment, 2),
            loan.account_id,
            loan.notes,
        )
    )
    await db.commit()
    
    return await get_loan(db, cursor.lastrowid)


async def get_loan(db: aiosqlite.Connection, loan_id: int) -> Optional[LoanResponse]:
    """Get a single loan by ID."""
    cursor = await db.execute(
        """
        SELECT 
            l.*,
            a.name as account_name
        FROM loans l
        LEFT JOIN accounts a ON l.account_id = a.id
        WHERE l.id = ?
        """,
        (loan_id,)
    )
    row = await cursor.fetchone()
    
    if not row:
        return None
    
    return _row_to_loan_response(dict(row))


async def get_all_loans(
    db: aiosqlite.Connection,
    is_active: Optional[bool] = None
) -> LoanListResponse:
    """Get all loans with optional active filter."""
    query = """
        SELECT 
            l.*,
            a.name as account_name
        FROM loans l
        LEFT JOIN accounts a ON l.account_id = a.id
        WHERE 1=1
    """
    params = []
    
    if is_active is not None:
        query += " AND l.is_active = ?"
        params.append(1 if is_active else 0)
    
    query += " ORDER BY l.created_at DESC"
    
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    
    loans = [_row_to_loan_response(dict(row)) for row in rows]
    
    total_balance = sum(loan.current_balance for loan in loans if loan.is_active)
    total_original = sum(loan.original_principal for loan in loans if loan.is_active)
    
    return LoanListResponse(
        loans=loans,
        total=len(loans),
        total_balance=round(total_balance, 2),
        total_original=round(total_original, 2),
    )


async def get_loan_summary(db: aiosqlite.Connection) -> LoanSummary:
    """Get summary of all loans for dashboard."""
    cursor = await db.execute(
        """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN is_active = 1 THEN current_balance ELSE 0 END) as total_balance,
            SUM(CASE WHEN is_active = 1 THEN original_principal ELSE 0 END) as total_original,
            SUM(CASE WHEN is_active = 1 THEN monthly_payment ELSE 0 END) as total_monthly
        FROM loans
        """
    )
    row = await cursor.fetchone()
    row_dict = dict(row)
    
    cursor = await db.execute(
        """
        SELECT loan_type, COUNT(*) as count
        FROM loans
        WHERE is_active = 1
        GROUP BY loan_type
        """
    )
    type_rows = await cursor.fetchall()
    loans_by_type = {r["loan_type"]: r["count"] for r in type_rows}
    
    return LoanSummary(
        total_loans=row_dict["total"] or 0,
        active_loans=row_dict["active"] or 0,
        total_balance=row_dict["total_balance"] or 0,
        total_original=row_dict["total_original"] or 0,
        total_monthly_payment=row_dict["total_monthly"] or 0,
        loans_by_type=loans_by_type,
    )


async def get_amortization_schedule(
    db: aiosqlite.Connection,
    loan_id: int
) -> Optional[AmortizationSchedule]:
    """Get the full amortization schedule for a loan."""
    loan = await get_loan(db, loan_id)
    if not loan:
        return None
    
    schedule = generate_amortization_schedule(
        loan.original_principal,
        loan.interest_rate,
        loan.term_months,
        loan.start_date,
        loan.monthly_payment,
    )
    
    total_interest = sum(entry.interest for entry in schedule)
    total_cost = loan.original_principal + total_interest
    
    return AmortizationSchedule(
        loan_id=loan.id,
        loan_name=loan.name,
        original_principal=loan.original_principal,
        interest_rate=loan.interest_rate,
        term_months=loan.term_months,
        monthly_payment=loan.monthly_payment,
        total_interest=round(total_interest, 2),
        total_cost=round(total_cost, 2),
        schedule=schedule,
    )


async def update_loan(
    db: aiosqlite.Connection,
    loan_id: int,
    update: LoanUpdate
) -> Optional[LoanResponse]:
    """Update a loan."""
    update_data = update.model_dump(exclude_unset=True)
    
    if not update_data:
        return await get_loan(db, loan_id)
    
    if "is_active" in update_data:
        update_data["is_active"] = 1 if update_data["is_active"] else 0
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values()) + [loan_id]
    
    await db.execute(
        f"UPDATE loans SET {set_clause} WHERE id = ?",
        values
    )
    await db.commit()
    
    return await get_loan(db, loan_id)


async def delete_loan(db: aiosqlite.Connection, loan_id: int) -> bool:
    """Delete a loan and its payment history."""
    cursor = await db.execute(
        "DELETE FROM loans WHERE id = ?",
        (loan_id,)
    )
    await db.commit()
    
    return cursor.rowcount > 0


async def record_payment(
    db: aiosqlite.Connection,
    loan_id: int,
    payment: LoanPayment
) -> Optional[LoanPaymentResponse]:
    """
    Record a loan payment and update the loan balance.
    """
    loan = await get_loan(db, loan_id)
    if not loan:
        return None
    
    monthly_rate = (loan.interest_rate / 100) / 12
    interest_portion = loan.current_balance * monthly_rate
    
    base_principal = payment.amount - interest_portion
    total_principal = base_principal + payment.extra_principal
    
    if total_principal > loan.current_balance:
        total_principal = loan.current_balance
        interest_portion = payment.amount - total_principal
    
    new_balance = max(0, loan.current_balance - total_principal)
    
    cursor = await db.execute(
        """
        INSERT INTO loan_payments (
            loan_id, amount, principal_paid, interest_paid,
            extra_principal, balance_after, payment_date, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            loan_id,
            payment.amount + payment.extra_principal,
            round(total_principal, 2),
            round(interest_portion, 2),
            payment.extra_principal,
            round(new_balance, 2),
            payment.payment_date.isoformat(),
            payment.notes,
        )
    )
    payment_id = cursor.lastrowid
    
    total_payment = payment.amount + payment.extra_principal
    is_active = 1 if new_balance > 0.01 else 0
    
    await db.execute(
        """
        UPDATE loans 
        SET current_balance = ?, 
            total_paid = total_paid + ?,
            is_active = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            round(new_balance, 2),
            round(total_payment, 2),
            is_active,
            datetime.now().isoformat(),
            loan_id,
        )
    )
    await db.commit()
    
    cursor = await db.execute(
        "SELECT * FROM loan_payments WHERE id = ?",
        (payment_id,)
    )
    row = await cursor.fetchone()
    row_dict = dict(row)
    
    return LoanPaymentResponse(
        id=row_dict["id"],
        loan_id=row_dict["loan_id"],
        amount=row_dict["amount"],
        principal_paid=row_dict["principal_paid"],
        interest_paid=row_dict["interest_paid"],
        extra_principal=row_dict["extra_principal"],
        new_balance=row_dict["balance_after"],
        payment_date=date.fromisoformat(row_dict["payment_date"]),
        notes=row_dict.get("notes"),
        created_at=datetime.fromisoformat(row_dict["created_at"]) if row_dict.get("created_at") else datetime.now(),
    )


async def get_loan_payments(
    db: aiosqlite.Connection,
    loan_id: int,
    limit: int = 50
) -> list[LoanPaymentResponse]:
    """Get payment history for a loan."""
    cursor = await db.execute(
        """
        SELECT * FROM loan_payments
        WHERE loan_id = ?
        ORDER BY payment_date DESC, id DESC
        LIMIT ?
        """,
        (loan_id, limit)
    )
    rows = await cursor.fetchall()
    
    payments = []
    for row in rows:
        row_dict = dict(row)
        payments.append(LoanPaymentResponse(
            id=row_dict["id"],
            loan_id=row_dict["loan_id"],
            amount=row_dict["amount"],
            principal_paid=row_dict["principal_paid"],
            interest_paid=row_dict["interest_paid"],
            extra_principal=row_dict["extra_principal"],
            new_balance=row_dict["balance_after"],
            payment_date=date.fromisoformat(row_dict["payment_date"]),
            notes=row_dict.get("notes"),
            created_at=datetime.fromisoformat(row_dict["created_at"]) if row_dict.get("created_at") else datetime.now(),
        ))
    
    return payments


def _row_to_loan_response(row: dict) -> LoanResponse:
    """Convert a database row to a LoanResponse."""
    start_date = row.get("start_date")
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    
    created_at = row.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    updated_at = row.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    return LoanResponse(
        id=row["id"],
        name=row["name"],
        loan_type=row["loan_type"],
        original_principal=row["original_principal"],
        current_balance=row["current_balance"],
        interest_rate=row["interest_rate"],
        term_months=row["term_months"],
        start_date=start_date,
        monthly_payment=row.get("monthly_payment"),
        total_paid=row.get("total_paid", 0),
        account_id=row.get("account_id"),
        account_name=row.get("account_name"),
        notes=row.get("notes"),
        is_active=bool(row["is_active"]),
        created_at=created_at or datetime.now(),
        updated_at=updated_at or datetime.now(),
    )