# Transaction Tracker

A personal finance web application for tracking accounts, transactions, subscriptions, and loans. Built with FastAPI and SQLite.

## Features

- **Accounts** -- Manage bank accounts, credit cards, loans, and investments with real-time balance tracking.
- **Transactions** -- Record income, expenses, and transfers with filtering, search, and pagination.
- **Subscriptions** -- Track recurring payments with billing cycle support and renewal reminders.
- **Loans** -- Monitor loan balances, record payments, and view amortization schedules.
- **Reports** -- View spending breakdowns by category, monthly trends, and export data to CSV.
- **Dashboard** -- Overview of net worth, recent transactions, upcoming renewals, and loan summaries.

## Tech Stack

- **Backend:** FastAPI, aiosqlite (SQLite), Jinja2 templates
- **Frontend:** Vanilla JavaScript, Feather Icons, Chart.js (reports)
- **Auth:** JWT via HTTP-only cookies (passlib + python-jose)

## Setup

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
```

## Running

```sh
uv run uvicorn app.main:app --reload
```

The app will be available at `http://localhost:8000`. On first launch the database is created automatically in `data/tracker.db`.

## Project Structure

```
app/
  main.py            Application entry point
  config.py          Settings and constants
  database.py        SQLite schema and connection helpers
  api/
    dependencies.py  Auth and DB dependencies
    routes/          API and page route handlers
    schemas/         Pydantic request/response models
    services/        Business logic
  static/            CSS and JavaScript
  templates/         Jinja2 HTML templates
data/                SQLite database (created at runtime)
```
