# Transaction Tracker

A personal finance tracking application with a FastAPI backend, desktop GUI, and Progressive Web App (PWA) for mobile access.

## Features

- **Account Management**: Track credit cards, checking accounts, savings accounts, and cash
- **Transaction Logging**: Manually log all your transactions (income and expenses)
- **Credit Card Monitoring**: See spending vs credit limit with utilization percentages
- **Category Tracking**: Organize transactions by category
- **Subscription Management**: Track recurring payments and billing dates
- **Budget System**: Create and monitor monthly budgets (coming soon)
- **Cross-Platform**: Access from desktop GUI or iPhone via PWA

## Project Structure

```
transaction-tracker/
├── backend/           # FastAPI server
│   └── app/
│       ├── main.py       # FastAPI application entry point
│       ├── database.py   # SQLite database configuration
│       ├── models.py     # SQLAlchemy database models
│       ├── schemas.py    # Pydantic validation schemas
│       └── routers/      # API route handlers
├── desktop/           # Tkinter desktop application
│   ├── main.py           # Desktop GUI application
│   └── api_client.py     # API client library
├── pwa/               # Progressive Web App
│   ├── index.html        # Main HTML file
│   ├── manifest.json     # PWA manifest
│   ├── sw.js             # Service worker
│   ├── css/style.css     # Styles
│   └── js/app.js         # JavaScript application
├── pyproject.toml     # Project dependencies (uv)
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

To install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Set Up the Backend

```bash
# From the project root directory, sync dependencies
uv sync

# Start the server
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

**Important**: Using `--host 0.0.0.0` allows access from other devices on your network.

### 2. Run the Desktop Application

```bash
# Run the desktop app (dependencies already installed via uv sync)
uv run python desktop/main.py
```

### 3. Access the PWA on iPhone

To access the PWA from your iPhone:

1. **Find your computer's local IP address**:
   ```bash
   # On macOS
   ipconfig getifaddr en0
   
   # Example output: 192.168.1.100
   ```

2. **Serve the PWA files** (from the project root):
   ```bash
   cd pwa
   uv run python -m http.server 8080
   ```

3. **On your iPhone**:
   - Make sure you're connected to the same WiFi network
   - Open Safari and go to `http://YOUR_IP:8080` (e.g., `http://192.168.1.100:8080`)
   - Tap the Share button → "Add to Home Screen"
   - Open the app and go to Settings (⚙️ icon)
   - Set the API URL to `http://YOUR_IP:8000`

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/accounts/` | GET, POST | List/create accounts |
| `/accounts/{id}` | GET, PUT, DELETE | Manage specific account |
| `/transactions/` | GET, POST | List/create transactions |
| `/transactions/{id}` | GET, PUT, DELETE | Manage specific transaction |
| `/categories/` | GET, POST | List/create categories |
| `/subscriptions/` | GET, POST | List/create subscriptions |
| `/dashboard/summary` | GET | Get monthly summary |
| `/dashboard/credit-cards` | GET | Get credit card overview |

## Usage Guide

### Adding an Account

1. Go to the **Accounts** tab
2. Click **+ Add Account**
3. Enter the account name, type, and credit limit (for credit cards)
4. Click **Save**

### Logging a Transaction

1. Go to the **Transactions** tab
2. Click **+ Add Transaction**
3. Enter the amount, description, date, account, and category
4. Check "This is income" for income transactions
5. Click **Save**

### Tracking Credit Card Usage

The **Dashboard** shows:
- Total income, expenses, and net for the current month
- Credit card utilization bars (green < 70%, yellow 70-90%, red > 90%)
- Recent transactions

### Managing Subscriptions

1. Go to the **Subscriptions** tab
2. Add subscriptions with their billing cycle and next billing date
3. Click **Paid** when you pay a subscription to update the next billing date

## Default Categories

The app comes with pre-configured categories:
- Food & Dining
- Transportation
- Shopping
- Entertainment
- Bills & Utilities
- Healthcare
- Travel
- Education
- Personal Care
- Subscriptions
- Groceries
- Income
- Other

## Data Storage

- All data is stored locally in `transactions.db` (SQLite database) in the project root
- No data is sent to external servers
- Back up this file to preserve your data

## Security Notes

⚠️ **This app is designed for local/home network use only.**

- The API allows all origins (CORS) for convenience
- There is no authentication - anyone on your network can access the API
- For secure remote access, consider using a VPN or SSH tunnel

## Troubleshooting

### "Could not connect to server"

1. Make sure the FastAPI backend is running
2. Check the API URL in settings
3. If on iPhone, make sure you're on the same WiFi network

### PWA not installing on iPhone

1. Must use Safari (not Chrome/Firefox)
2. Go to Share → Add to Home Screen
3. The manifest.json must be properly served

### Database errors

Delete `transactions.db` from the project root to reset the database (you'll lose all data).

## Future Enhancements

- [ ] Budget tracking with category allocations
- [ ] Monthly/yearly reports and charts
- [ ] Data export (CSV, PDF)
- [ ] Recurring transaction automation
- [ ] Multiple currency support
- [ ] Data sync across devices

## License

This project is for personal use. Feel free to modify and extend it for your needs.
