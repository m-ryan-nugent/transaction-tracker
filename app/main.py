"""Transaction Tracker API"""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import APP_NAME, APP_VERSION
from app.database import get_db as db_connect
from app.database import init_db, seed_categories
from app.api.services.auth_service import user_exists
from app.api.dependencies import get_optional_user
from app.api.routes import (
    auth,
    accounts,
    categories,
    transactions,
    subscriptions,
    loans,
    reports,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    await init_db()
    await seed_categories()
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


app.include_router(auth.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(subscriptions.router)
app.include_router(loans.router)
app.include_router(reports.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - redirects to login or dashboard based on auth status."""
    db = await db_connect()
    try:
        if not await user_exists(db):
            return RedirectResponse(url="/setup", status_code=302)

        user = await get_optional_user(request, None, db)

        if user:
            return RedirectResponse(url="/dashboard", status_code=302)
        else:
            return RedirectResponse(url="/login", status_code=302)
    finally:
        await db.close()


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """Initial setup page for creating the first user."""
    return templates.TemplateResponse("setup.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """Accounts management page."""
    return templates.TemplateResponse("accounts.html", {"request": request})


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    """Transactions page."""
    return templates.TemplateResponse("transactions.html", {"request": request})


@app.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_page(request: Request):
    """Subscriptions management page."""
    return templates.TemplateResponse("subscriptions.html", {"request": request})


@app.get("/loans", response_class=HTMLResponse)
async def loans_page(request: Request):
    """Loans management page."""
    return templates.TemplateResponse("loans.html", {"request": request})


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports and analytics page."""
    return templates.TemplateResponse("reports.html", {"request": request})
