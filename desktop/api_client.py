"""API client for communicating with the backend."""
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime


class APIClient:
    """Client for interacting with the Transaction Tracker API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return None
            return response.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Could not connect to API at {self.base_url}")
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_detail = e.response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            raise Exception(f"API Error: {error_detail}")
    
    # Health check
    def health_check(self) -> Dict:
        """Check if the API is healthy."""
        return self._request("GET", "/health")
    
    # Accounts
    def get_accounts(self, include_inactive: bool = False) -> List[Dict]:
        """Get all accounts."""
        params = {"include_inactive": include_inactive}
        return self._request("GET", "/accounts/", params=params)
    
    def create_account(self, name: str, account_type: str, 
                       credit_limit: Optional[float] = None,
                       current_balance: float = 0.0) -> Dict:
        """Create a new account."""
        data = {
            "name": name,
            "account_type": account_type,
            "current_balance": current_balance
        }
        if credit_limit is not None:
            data["credit_limit"] = credit_limit
        return self._request("POST", "/accounts/", json=data)
    
    def get_account(self, account_id: int) -> Dict:
        """Get a specific account."""
        return self._request("GET", f"/accounts/{account_id}")
    
    def update_account(self, account_id: int, **kwargs) -> Dict:
        """Update an account."""
        return self._request("PUT", f"/accounts/{account_id}", json=kwargs)
    
    def delete_account(self, account_id: int) -> None:
        """Delete an account."""
        self._request("DELETE", f"/accounts/{account_id}")
    
    def get_account_summary(self, account_id: int, 
                            month: Optional[int] = None,
                            year: Optional[int] = None) -> Dict:
        """Get account summary."""
        params = {}
        if month:
            params["month"] = month
        if year:
            params["year"] = year
        return self._request("GET", f"/accounts/{account_id}/summary", params=params)
    
    # Transactions
    def get_transactions(self, account_id: Optional[int] = None,
                         category_id: Optional[int] = None,
                         is_income: Optional[bool] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100) -> List[Dict]:
        """Get transactions with optional filters."""
        params = {"limit": limit}
        if account_id:
            params["account_id"] = account_id
        if category_id:
            params["category_id"] = category_id
        if is_income is not None:
            params["is_income"] = is_income
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._request("GET", "/transactions/", params=params)
    
    def create_transaction(self, amount: float, description: str,
                           account_id: int, date: datetime,
                           category_id: Optional[int] = None,
                           is_income: bool = False,
                           notes: Optional[str] = None) -> Dict:
        """Create a new transaction."""
        data = {
            "amount": amount,
            "description": description,
            "account_id": account_id,
            "date": date.isoformat(),
            "is_income": is_income
        }
        if category_id:
            data["category_id"] = category_id
        if notes:
            data["notes"] = notes
        return self._request("POST", "/transactions/", json=data)
    
    def delete_transaction(self, transaction_id: int) -> None:
        """Delete a transaction."""
        self._request("DELETE", f"/transactions/{transaction_id}")
    
    # Categories
    def get_categories(self) -> List[Dict]:
        """Get all categories."""
        return self._request("GET", "/categories/")
    
    def create_category(self, name: str, color: str = "#6366f1",
                        is_income: bool = False) -> Dict:
        """Create a new category."""
        data = {
            "name": name,
            "color": color,
            "is_income": is_income
        }
        return self._request("POST", "/categories/", json=data)
    
    # Subscriptions
    def get_subscriptions(self, include_inactive: bool = False) -> List[Dict]:
        """Get all subscriptions."""
        params = {"include_inactive": include_inactive}
        return self._request("GET", "/subscriptions/", params=params)
    
    def create_subscription(self, name: str, amount: float,
                            billing_cycle: str, next_billing_date: datetime,
                            account_id: Optional[int] = None,
                            category_id: Optional[int] = None,
                            notes: Optional[str] = None) -> Dict:
        """Create a new subscription."""
        data = {
            "name": name,
            "amount": amount,
            "billing_cycle": billing_cycle,
            "next_billing_date": next_billing_date.isoformat()
        }
        if account_id:
            data["account_id"] = account_id
        if category_id:
            data["category_id"] = category_id
        if notes:
            data["notes"] = notes
        return self._request("POST", "/subscriptions/", json=data)
    
    def delete_subscription(self, subscription_id: int) -> None:
        """Delete a subscription."""
        self._request("DELETE", f"/subscriptions/{subscription_id}")
    
    def mark_subscription_paid(self, subscription_id: int) -> Dict:
        """Mark a subscription as paid."""
        return self._request("POST", f"/subscriptions/{subscription_id}/mark-paid")
    
    # Dashboard
    def get_monthly_summary(self, month: Optional[int] = None,
                            year: Optional[int] = None) -> Dict:
        """Get monthly summary."""
        params = {}
        if month:
            params["month"] = month
        if year:
            params["year"] = year
        return self._request("GET", "/dashboard/summary", params=params)
    
    def get_credit_card_overview(self, month: Optional[int] = None,
                                  year: Optional[int] = None) -> List[Dict]:
        """Get credit card overview."""
        params = {}
        if month:
            params["month"] = month
        if year:
            params["year"] = year
        return self._request("GET", "/dashboard/credit-cards", params=params)
    
    def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """Get recent transactions."""
        return self._request("GET", "/dashboard/recent-transactions", params={"limit": limit})
