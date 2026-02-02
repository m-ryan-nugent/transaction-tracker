"""Report service"""

import io
import csv
from typing import Optional
from datetime import date
from dateutil.relativedelta import relativedelta

import aiosqlite

from app.api.schemas.report import (
    CategorySpending,
    SpendingByCategory,
    MonthlyTrend,
    SpendingTrends,
    NetWorthDataPoint,
    NetWorthHistory,
)


MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


async def get_spending_by_category(
    db: aiosqlite.Connection,
    start_date: date,
    end_date: date,
    account_id: Optional[int] = None,
) -> SpendingByCategory:
    """
    Get spending breakdown by category for a date range.
    """
    query = """
        SELECT 
            c.id as category_id,
            COALESCE(c.name, 'Uncategorized') as category_name,
            SUM(ABS(t.amount)) as total,
            COUNT(*) as count
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.amount < 0
            AND t.date >= ?
            AND t.date <= ?
            AND t.transfer_to_account_id IS NULL
    """
    params = [start_date.isoformat(), end_date.isoformat()]
    
    if account_id:
        query += " AND t.account_id = ?"
        params.append(account_id)
    
    query += " GROUP BY c.id, c.name ORDER BY total DESC"
    
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    
    total_spending = sum(row["total"] for row in rows)
    
    categories = []
    for row in rows:
        percent = (row["total"] / total_spending * 100) if total_spending > 0 else 0
        categories.append(CategorySpending(
            category_id=row["category_id"],
            category_name=row["category_name"],
            total=round(row["total"], 2),
            count=row["count"],
            percent=round(percent, 1),
        ))
    
    income_query = """
        SELECT COALESCE(SUM(t.amount), 0) as total
        FROM transactions t
        WHERE t.amount > 0
            AND t.date >= ?
            AND t.date <= ?
            AND t.transfer_to_account_id IS NULL
    """
    income_params = [start_date.isoformat(), end_date.isoformat()]
    if account_id:
        income_query += " AND t.account_id = ?"
        income_params.append(account_id)
    
    cursor = await db.execute(income_query, income_params)
    income_row = await cursor.fetchone()
    total_income = income_row["total"] or 0
    
    return SpendingByCategory(
        start_date=start_date,
        end_date=end_date,
        total_spending=round(total_spending, 2),
        total_income=round(total_income, 2),
        net=round(total_income - total_spending, 2),
        categories=categories,
    )


async def get_spending_trends(
    db: aiosqlite.Connection,
    months: int = 12,
    account_id: Optional[int] = None,
) -> SpendingTrends:
    """
    Get monthly spending and income trends.
    """
    today = date.today()
    start_date = (today - relativedelta(months=months-1)).replace(day=1)
    
    query = """
        SELECT 
            strftime('%Y', t.date) as year,
            strftime('%m', t.date) as month,
            SUM(CASE WHEN t.amount > 0 AND t.transfer_to_account_id IS NULL THEN t.amount ELSE 0 END) as income,
            SUM(CASE WHEN t.amount < 0 AND t.transfer_to_account_id IS NULL THEN ABS(t.amount) ELSE 0 END) as expenses
        FROM transactions t
        WHERE t.date >= ?
    """
    params = [start_date.isoformat()]
    
    if account_id:
        query += " AND t.account_id = ?"
        params.append(account_id)
    
    query += " GROUP BY year, month ORDER BY year, month"
    
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    
    monthly_data = []
    for row in rows:
        year = int(row["year"])
        month = int(row["month"])
        income = row["income"] or 0
        expenses = row["expenses"] or 0
        
        monthly_data.append(MonthlyTrend(
            year=year,
            month=month,
            month_name=MONTH_NAMES[month],
            income=round(income, 2),
            expenses=round(expenses, 2),
            net=round(income - expenses, 2),
        ))
    
    if monthly_data:
        avg_income = sum(m.income for m in monthly_data) / len(monthly_data)
        avg_expenses = sum(m.expenses for m in monthly_data) / len(monthly_data)
    else:
        avg_income = 0
        avg_expenses = 0
    
    return SpendingTrends(
        months=monthly_data,
        average_income=round(avg_income, 2),
        average_expenses=round(avg_expenses, 2),
    )


async def get_net_worth_history(
    db: aiosqlite.Connection,
    months: int = 12,
) -> NetWorthHistory:
    """
    Get net worth history over time.
    """
    cursor = await db.execute("""
        SELECT 
            SUM(CASE WHEN account_type IN ('bank', 'investment') THEN current_balance ELSE 0 END) as assets,
            SUM(CASE WHEN account_type IN ('credit_card', 'loan') THEN ABS(current_balance) ELSE 0 END) as liabilities
        FROM accounts
        WHERE is_active = 1
    """)
    row = await cursor.fetchone()
    current_assets = row["assets"] or 0
    current_liabilities = row["liabilities"] or 0
    current_net_worth = current_assets - current_liabilities
    
    cursor = await db.execute("""
        SELECT COALESCE(SUM(current_balance), 0) as total
        FROM loans
        WHERE is_active = 1
    """)
    loan_row = await cursor.fetchone()
    loan_balance = loan_row["total"] or 0
    current_liabilities += loan_balance
    current_net_worth = current_assets - current_liabilities
    
    today = date.today()
    
    history = [NetWorthDataPoint(
        date=today,
        assets=round(current_assets, 2),
        liabilities=round(current_liabilities, 2),
        net_worth=round(current_net_worth, 2),
    )]
    
    change_amount = 0
    change_percent = 0
    
    return NetWorthHistory(
        history=history,
        current_net_worth=round(current_net_worth, 2),
        change_amount=round(change_amount, 2),
        change_percent=round(change_percent, 1),
    )


async def export_transactions_csv(
    db: aiosqlite.Connection,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
) -> str:
    """
    Export transactions to CSV format.
    """
    query = """
        SELECT 
            t.date,
            t.amount,
            t.description,
            t.payee,
            a.name as account_name,
            c.name as category_name,
            ta.name as transfer_to,
            t.notes
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts ta ON t.transfer_to_account_id = ta.id
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND t.date >= ?"
        params.append(start_date.isoformat())
    
    if end_date:
        query += " AND t.date <= ?"
        params.append(end_date.isoformat())
    
    if account_id:
        query += " AND (t.account_id = ? OR t.transfer_to_account_id = ?)"
        params.extend([account_id, account_id])
    
    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    
    query += " ORDER BY t.date DESC, t.id DESC"
    
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Date", "Amount", "Description", "Payee", 
        "Account", "Category", "Transfer To", "Notes"
    ])
    
    for row in rows:
        writer.writerow([
            row["date"],
            row["amount"],
            row["description"] or "",
            row["payee"] or "",
            row["account_name"] or "",
            row["category_name"] or "",
            row["transfer_to"] or "",
            row["notes"] or "",
        ])
    
    return output.getvalue()


async def export_accounts_csv(db: aiosqlite.Connection) -> str:
    """Export accounts to CSV format."""
    cursor = await db.execute("""
        SELECT 
            name, account_type, current_balance, credit_limit,
            interest_rate, institution, notes, is_active
        FROM accounts
        ORDER BY account_type, name
    """)
    rows = await cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Name", "Type", "Balance", "Credit Limit",
        "Interest Rate", "Institution", "Notes", "Active"
    ])
    
    for row in rows:
        writer.writerow([
            row["name"],
            row["account_type"],
            row["current_balance"],
            row["credit_limit"] or "",
            row["interest_rate"] or "",
            row["institution"] or "",
            row["notes"] or "",
            "Yes" if row["is_active"] else "No",
        ])
    
    return output.getvalue()


async def export_subscriptions_csv(db: aiosqlite.Connection) -> str:
    """Export subscriptions to CSV format."""
    cursor = await db.execute("""
        SELECT 
            s.name, s.amount, s.billing_cycle, s.next_billing_date,
            a.name as account_name, c.name as category_name,
            s.notes, s.is_active
        FROM subscriptions s
        LEFT JOIN accounts a ON s.account_id = a.id
        LEFT JOIN categories c ON s.category_id = c.id
        ORDER BY s.next_billing_date
    """)
    rows = await cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Name", "Amount", "Billing Cycle", "Next Billing Date",
        "Account", "Category", "Notes", "Active"
    ])
    
    for row in rows:
        writer.writerow([
            row["name"],
            row["amount"],
            row["billing_cycle"],
            row["next_billing_date"],
            row["account_name"] or "",
            row["category_name"] or "",
            row["notes"] or "",
            "Yes" if row["is_active"] else "No",
        ])
    
    return output.getvalue()


async def export_loans_csv(db: aiosqlite.Connection) -> str:
    """Export loans to CSV format."""
    cursor = await db.execute("""
        SELECT 
            l.name, l.loan_type, l.original_principal, l.current_balance,
            l.interest_rate, l.term_months, l.start_date, l.monthly_payment,
            l.total_paid, a.name as account_name, l.notes, l.is_active
        FROM loans l
        LEFT JOIN accounts a ON l.account_id = a.id
        ORDER BY l.start_date DESC
    """)
    rows = await cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Name", "Type", "Original Principal", "Current Balance",
        "Interest Rate", "Term (Months)", "Start Date", "Monthly Payment",
        "Total Paid", "Account", "Notes", "Active"
    ])
    
    for row in rows:
        writer.writerow([
            row["name"],
            row["loan_type"],
            row["original_principal"],
            row["current_balance"],
            row["interest_rate"],
            row["term_months"],
            row["start_date"],
            row["monthly_payment"] or "",
            row["total_paid"],
            row["account_name"] or "",
            row["notes"] or "",
            "Yes" if row["is_active"] else "No",
        ])
    
    return output.getvalue()