"""Transaction Tracker Desktop Application."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Optional
import threading

from api_client import APIClient


class TransactionTrackerApp:
    """Main application class."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Transaction Tracker")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)
        
        # API client
        self.api = APIClient("http://localhost:8000")
        
        # Data caches
        self.accounts = []
        self.categories = []
        self.transactions = []
        
        # Setup UI
        self._setup_styles()
        self._create_menu()
        self._create_main_layout()
        
        # Initial data load
        self.root.after(100, self._initial_load)
    
    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure("TFrame", background="#f8fafc")
        style.configure("TLabel", background="#f8fafc", font=("Helvetica", 11))
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Subtitle.TLabel", font=("Helvetica", 13, "bold"))
        style.configure("TButton", font=("Helvetica", 10), padding=5)
        style.configure("Accent.TButton", font=("Helvetica", 10, "bold"))
        
        # Treeview styling
        style.configure("Treeview", font=("Helvetica", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
    
    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Data", command=self._refresh_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_main_layout(self):
        """Create the main application layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self._create_dashboard_tab()
        self._create_transactions_tab()
        self._create_accounts_tab()
        self._create_subscriptions_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Connecting to server...")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def _create_dashboard_tab(self):
        """Create the dashboard tab."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Dashboard")
        
        # Header
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header, text="Monthly Overview", style="Title.TLabel").pack(side=tk.LEFT)
        
        # Month selector
        month_frame = ttk.Frame(header)
        month_frame.pack(side=tk.RIGHT)
        
        now = datetime.now()
        self.dash_month_var = tk.StringVar(value=str(now.month))
        self.dash_year_var = tk.StringVar(value=str(now.year))
        
        ttk.Label(month_frame, text="Month:").pack(side=tk.LEFT, padx=(0, 5))
        month_combo = ttk.Combobox(month_frame, textvariable=self.dash_month_var, 
                                   values=[str(i) for i in range(1, 13)], width=5)
        month_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(month_frame, text="Year:").pack(side=tk.LEFT, padx=(0, 5))
        year_combo = ttk.Combobox(month_frame, textvariable=self.dash_year_var,
                                  values=[str(i) for i in range(2020, 2031)], width=6)
        year_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(month_frame, text="Refresh", 
                   command=self._refresh_dashboard).pack(side=tk.LEFT)
        
        # Summary cards
        cards_frame = ttk.Frame(tab)
        cards_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Income card
        self.income_card = self._create_summary_card(cards_frame, "Income", "$0.00", "#10b981")
        self.income_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Expenses card
        self.expenses_card = self._create_summary_card(cards_frame, "Expenses", "$0.00", "#ef4444")
        self.expenses_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Net card
        self.net_card = self._create_summary_card(cards_frame, "Net", "$0.00", "#3b82f6")
        self.net_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Credit cards section
        cc_frame = ttk.LabelFrame(tab, text="Credit Card Utilization", padding="10")
        cc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.cc_tree = ttk.Treeview(cc_frame, columns=("limit", "spent", "remaining", "util"),
                                     show="headings", height=5)
        self.cc_tree.heading("limit", text="Credit Limit")
        self.cc_tree.heading("spent", text="Spent")
        self.cc_tree.heading("remaining", text="Remaining")
        self.cc_tree.heading("util", text="Utilization")
        self.cc_tree.column("limit", width=120)
        self.cc_tree.column("spent", width=120)
        self.cc_tree.column("remaining", width=120)
        self.cc_tree.column("util", width=100)
        self.cc_tree.pack(fill=tk.BOTH, expand=True)
        
        # Recent transactions
        recent_frame = ttk.LabelFrame(tab, text="Recent Transactions", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True)
        
        self.recent_tree = ttk.Treeview(recent_frame, 
                                         columns=("date", "description", "amount"),
                                         show="headings", height=5)
        self.recent_tree.heading("date", text="Date")
        self.recent_tree.heading("description", text="Description")
        self.recent_tree.heading("amount", text="Amount")
        self.recent_tree.column("date", width=100)
        self.recent_tree.column("description", width=300)
        self.recent_tree.column("amount", width=100)
        self.recent_tree.pack(fill=tk.BOTH, expand=True)
    
    def _create_summary_card(self, parent, title: str, value: str, color: str) -> ttk.Frame:
        """Create a summary card widget."""
        card = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        
        ttk.Label(card, text=title, style="Subtitle.TLabel").pack(pady=(10, 5))
        
        value_label = ttk.Label(card, text=value, font=("Helvetica", 24, "bold"))
        value_label.pack(pady=(0, 10))
        card.value_label = value_label
        
        return card
    
    def _create_transactions_tab(self):
        """Create the transactions tab."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Transactions")
        
        # Header with add button
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header, text="Transactions", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Button(header, text="+ Add Transaction", 
                   command=self._show_add_transaction_dialog).pack(side=tk.RIGHT)
        
        # Filters
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Account:").pack(side=tk.LEFT, padx=(0, 5))
        self.trans_account_var = tk.StringVar(value="All")
        self.trans_account_combo = ttk.Combobox(filter_frame, textvariable=self.trans_account_var,
                                                 values=["All"], width=20)
        self.trans_account_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(filter_frame, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.trans_type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(filter_frame, textvariable=self.trans_type_var,
                                  values=["All", "Income", "Expense"], width=10)
        type_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(filter_frame, text="Apply Filter", 
                   command=self._refresh_transactions).pack(side=tk.LEFT)
        
        # Transactions list
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.trans_tree = ttk.Treeview(list_frame, 
                                        columns=("date", "description", "category", "account", "amount"),
                                        show="headings")
        self.trans_tree.heading("date", text="Date")
        self.trans_tree.heading("description", text="Description")
        self.trans_tree.heading("category", text="Category")
        self.trans_tree.heading("account", text="Account")
        self.trans_tree.heading("amount", text="Amount")
        
        self.trans_tree.column("date", width=100)
        self.trans_tree.column("description", width=250)
        self.trans_tree.column("category", width=120)
        self.trans_tree.column("account", width=120)
        self.trans_tree.column("amount", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.trans_tree.yview)
        self.trans_tree.configure(yscrollcommand=scrollbar.set)
        
        self.trans_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Context menu
        self.trans_tree.bind("<Button-2>", self._show_transaction_context_menu)
        self.trans_tree.bind("<Button-3>", self._show_transaction_context_menu)
    
    def _create_accounts_tab(self):
        """Create the accounts tab."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Accounts")
        
        # Header
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header, text="Accounts", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Button(header, text="+ Add Account", 
                   command=self._show_add_account_dialog).pack(side=tk.RIGHT)
        
        # Accounts list
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.accounts_tree = ttk.Treeview(list_frame,
                                           columns=("type", "balance", "limit", "status"),
                                           show="headings")
        self.accounts_tree.heading("type", text="Type")
        self.accounts_tree.heading("balance", text="Balance")
        self.accounts_tree.heading("limit", text="Credit Limit")
        self.accounts_tree.heading("status", text="Status")
        
        self.accounts_tree.column("type", width=120)
        self.accounts_tree.column("balance", width=120)
        self.accounts_tree.column("limit", width=120)
        self.accounts_tree.column("status", width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)
        
        self.accounts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Context menu
        self.accounts_tree.bind("<Button-2>", self._show_account_context_menu)
        self.accounts_tree.bind("<Button-3>", self._show_account_context_menu)
    
    def _create_subscriptions_tab(self):
        """Create the subscriptions tab."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Subscriptions")
        
        # Header
        header = ttk.Frame(tab)
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header, text="Subscriptions", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Button(header, text="+ Add Subscription",
                   command=self._show_add_subscription_dialog).pack(side=tk.RIGHT)
        
        # Subscriptions list
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.subs_tree = ttk.Treeview(list_frame,
                                       columns=("amount", "cycle", "next_date", "status"),
                                       show="headings")
        self.subs_tree.heading("amount", text="Amount")
        self.subs_tree.heading("cycle", text="Billing Cycle")
        self.subs_tree.heading("next_date", text="Next Billing")
        self.subs_tree.heading("status", text="Status")
        
        self.subs_tree.column("amount", width=100)
        self.subs_tree.column("cycle", width=100)
        self.subs_tree.column("next_date", width=120)
        self.subs_tree.column("status", width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.subs_tree.yview)
        self.subs_tree.configure(yscrollcommand=scrollbar.set)
        
        self.subs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Context menu
        self.subs_tree.bind("<Button-2>", self._show_subscription_context_menu)
        self.subs_tree.bind("<Button-3>", self._show_subscription_context_menu)
    
    # Data loading methods
    def _initial_load(self):
        """Initial data load on startup."""
        try:
            self.api.health_check()
            self.status_var.set("Connected to server")
            self._refresh_all_data()
        except ConnectionError:
            self.status_var.set("Could not connect to server")
            messagebox.showerror("Connection Error", 
                               "Could not connect to the API server.\n\n"
                               "Make sure the server is running:\n"
                               "cd backend && uvicorn app.main:app --reload")
    
    def _refresh_all_data(self):
        """Refresh all data from the API."""
        try:
            self.accounts = self.api.get_accounts(include_inactive=True)
            self.categories = self.api.get_categories()
            self._update_account_combo()
            self._refresh_dashboard()
            self._refresh_transactions()
            self._refresh_accounts_list()
            self._refresh_subscriptions_list()
            self.status_var.set(f"Data refreshed at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
    
    def _update_account_combo(self):
        """Update account dropdown values."""
        account_names = ["All"] + [a["name"] for a in self.accounts if a["is_active"]]
        self.trans_account_combo["values"] = account_names
    
    def _refresh_dashboard(self):
        """Refresh dashboard data."""
        try:
            month = int(self.dash_month_var.get())
            year = int(self.dash_year_var.get())
            
            # Get summary
            summary = self.api.get_monthly_summary(month, year)
            
            # Update cards
            self.income_card.value_label.config(text=f"${summary['total_income']:,.2f}")
            self.expenses_card.value_label.config(text=f"${summary['total_expenses']:,.2f}")
            
            net = summary['net']
            net_text = f"${abs(net):,.2f}"
            if net < 0:
                net_text = f"-{net_text}"
            self.net_card.value_label.config(text=net_text)
            
            # Update credit cards
            self.cc_tree.delete(*self.cc_tree.get_children())
            cc_data = self.api.get_credit_card_overview(month, year)
            for cc in cc_data:
                util = f"{cc['utilization_percent']:.1f}%" if cc['utilization_percent'] else "N/A"
                self.cc_tree.insert("", "end", text=cc["name"], values=(
                    f"${cc['credit_limit']:,.2f}" if cc['credit_limit'] else "N/A",
                    f"${cc['spent_this_month']:,.2f}",
                    f"${cc['remaining_credit']:,.2f}" if cc['remaining_credit'] else "N/A",
                    util
                ))
            
            # Update recent transactions
            self.recent_tree.delete(*self.recent_tree.get_children())
            recent = self.api.get_recent_transactions(10)
            for t in recent:
                date = datetime.fromisoformat(t["date"]).strftime("%Y-%m-%d")
                amount = f"${t['amount']:,.2f}"
                if t["is_income"]:
                    amount = f"+{amount}"
                else:
                    amount = f"-{amount}"
                self.recent_tree.insert("", "end", values=(date, t["description"], amount))
                
        except Exception as e:
            self.status_var.set(f"Dashboard error: {str(e)}")
    
    def _refresh_transactions(self):
        """Refresh transactions list."""
        try:
            # Get filter values
            account_id = None
            if self.trans_account_var.get() != "All":
                for a in self.accounts:
                    if a["name"] == self.trans_account_var.get():
                        account_id = a["id"]
                        break
            
            is_income = None
            if self.trans_type_var.get() == "Income":
                is_income = True
            elif self.trans_type_var.get() == "Expense":
                is_income = False
            
            self.transactions = self.api.get_transactions(
                account_id=account_id,
                is_income=is_income,
                limit=200
            )
            
            # Update treeview
            self.trans_tree.delete(*self.trans_tree.get_children())
            for t in self.transactions:
                date = datetime.fromisoformat(t["date"]).strftime("%Y-%m-%d")
                category = t["category"]["name"] if t.get("category") else "Uncategorized"
                account = t["account"]["name"] if t.get("account") else "Unknown"
                amount = f"${t['amount']:,.2f}"
                if t["is_income"]:
                    amount = f"+{amount}"
                else:
                    amount = f"-{amount}"
                
                self.trans_tree.insert("", "end", iid=str(t["id"]), values=(
                    date, t["description"], category, account, amount
                ))
                
        except Exception as e:
            self.status_var.set(f"Transactions error: {str(e)}")
    
    def _refresh_accounts_list(self):
        """Refresh accounts list."""
        try:
            self.accounts_tree.delete(*self.accounts_tree.get_children())
            for a in self.accounts:
                type_display = a["account_type"].replace("_", " ").title()
                limit = f"${a['credit_limit']:,.2f}" if a.get("credit_limit") else "N/A"
                status = "Active" if a["is_active"] else "Inactive"
                
                self.accounts_tree.insert("", "end", iid=str(a["id"]), text=a["name"], values=(
                    type_display,
                    f"${a['current_balance']:,.2f}",
                    limit,
                    status
                ))
        except Exception as e:
            self.status_var.set(f"Accounts error: {str(e)}")
    
    def _refresh_subscriptions_list(self):
        """Refresh subscriptions list."""
        try:
            subs = self.api.get_subscriptions(include_inactive=True)
            self.subs_tree.delete(*self.subs_tree.get_children())
            
            for s in subs:
                next_date = datetime.fromisoformat(s["next_billing_date"]).strftime("%Y-%m-%d")
                status = "Active" if s["is_active"] else "Inactive"
                
                self.subs_tree.insert("", "end", iid=str(s["id"]), text=s["name"], values=(
                    f"${s['amount']:,.2f}",
                    s["billing_cycle"].title(),
                    next_date,
                    status
                ))
        except Exception as e:
            self.status_var.set(f"Subscriptions error: {str(e)}")
    
    # Dialog methods
    def _show_add_transaction_dialog(self):
        """Show dialog to add a new transaction."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Transaction")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Amount
        ttk.Label(frame, text="Amount:").pack(anchor=tk.W)
        amount_var = tk.StringVar()
        ttk.Entry(frame, textvariable=amount_var).pack(fill=tk.X, pady=(0, 10))
        
        # Description
        ttk.Label(frame, text="Description:").pack(anchor=tk.W)
        desc_var = tk.StringVar()
        ttk.Entry(frame, textvariable=desc_var).pack(fill=tk.X, pady=(0, 10))
        
        # Date
        ttk.Label(frame, text="Date (YYYY-MM-DD):").pack(anchor=tk.W)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(frame, textvariable=date_var).pack(fill=tk.X, pady=(0, 10))
        
        # Account
        ttk.Label(frame, text="Account:").pack(anchor=tk.W)
        account_var = tk.StringVar()
        account_names = [a["name"] for a in self.accounts if a["is_active"]]
        account_combo = ttk.Combobox(frame, textvariable=account_var, values=account_names)
        account_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Category
        ttk.Label(frame, text="Category:").pack(anchor=tk.W)
        category_var = tk.StringVar()
        category_names = [c["name"] for c in self.categories]
        category_combo = ttk.Combobox(frame, textvariable=category_var, values=category_names)
        category_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Is Income
        is_income_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="This is income", 
                        variable=is_income_var).pack(anchor=tk.W, pady=(0, 10))
        
        # Notes
        ttk.Label(frame, text="Notes (optional):").pack(anchor=tk.W)
        notes_var = tk.StringVar()
        ttk.Entry(frame, textvariable=notes_var).pack(fill=tk.X, pady=(0, 20))
        
        def save():
            try:
                amount = float(amount_var.get())
                description = desc_var.get().strip()
                date = datetime.strptime(date_var.get(), "%Y-%m-%d")
                
                # Find account ID
                account_id = None
                for a in self.accounts:
                    if a["name"] == account_var.get():
                        account_id = a["id"]
                        break
                
                if not account_id:
                    messagebox.showerror("Error", "Please select an account")
                    return
                
                # Find category ID
                category_id = None
                for c in self.categories:
                    if c["name"] == category_var.get():
                        category_id = c["id"]
                        break
                
                notes = notes_var.get().strip() or None
                
                self.api.create_transaction(
                    amount=amount,
                    description=description,
                    account_id=account_id,
                    date=date,
                    category_id=category_id,
                    is_income=is_income_var.get(),
                    notes=notes
                )
                
                dialog.destroy()
                self._refresh_all_data()
                self.status_var.set("Transaction added successfully")
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(frame, text="Save Transaction", command=save).pack(fill=tk.X)
    
    def _show_add_account_dialog(self):
        """Show dialog to add a new account."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Account")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(frame, text="Account Name:").pack(anchor=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var).pack(fill=tk.X, pady=(0, 10))
        
        # Type
        ttk.Label(frame, text="Account Type:").pack(anchor=tk.W)
        type_var = tk.StringVar(value="checking")
        type_combo = ttk.Combobox(frame, textvariable=type_var,
                                  values=["credit_card", "checking", "savings", "cash"])
        type_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Credit Limit (initially hidden)
        limit_frame = ttk.Frame(frame)
        ttk.Label(limit_frame, text="Credit Limit:").pack(anchor=tk.W)
        limit_var = tk.StringVar()
        ttk.Entry(limit_frame, textvariable=limit_var).pack(fill=tk.X, pady=(0, 10))
        
        # Balance with dynamic label
        balance_label = ttk.Label(frame, text="Initial Balance:")
        balance_label.pack(anchor=tk.W)
        balance_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=balance_var).pack(fill=tk.X, pady=(0, 5))
        balance_hint = ttk.Label(frame, text="", font=("Helvetica", 9), foreground="gray")
        balance_hint.pack(anchor=tk.W, pady=(0, 15))
        
        def on_type_change(event=None):
            if type_var.get() == "credit_card":
                limit_frame.pack(fill=tk.X, after=type_combo, pady=(0, 10))
                balance_label.config(text="Current Amount Owed:")
                balance_hint.config(text="How much you currently owe on this card")
            else:
                limit_frame.pack_forget()
                balance_label.config(text="Initial Balance:")
                balance_hint.config(text="")
        
        type_combo.bind("<<ComboboxSelected>>", on_type_change)
        on_type_change()  # Set initial state
        
        def save():
            try:
                name = name_var.get().strip()
                account_type = type_var.get()
                
                if not name:
                    messagebox.showerror("Error", "Please enter an account name")
                    return
                
                credit_limit = None
                if limit_var.get().strip():
                    credit_limit = float(limit_var.get())
                
                balance = float(balance_var.get()) if balance_var.get().strip() else 0.0
                
                self.api.create_account(
                    name=name,
                    account_type=account_type,
                    credit_limit=credit_limit,
                    current_balance=balance
                )
                
                dialog.destroy()
                self._refresh_all_data()
                self.status_var.set("Account added successfully")
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(frame, text="Save Account", command=save).pack(fill=tk.X)
    
    def _show_add_subscription_dialog(self):
        """Show dialog to add a new subscription."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Subscription")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(frame, text="Subscription Name:").pack(anchor=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var).pack(fill=tk.X, pady=(0, 10))
        
        # Amount
        ttk.Label(frame, text="Amount:").pack(anchor=tk.W)
        amount_var = tk.StringVar()
        ttk.Entry(frame, textvariable=amount_var).pack(fill=tk.X, pady=(0, 10))
        
        # Billing Cycle
        ttk.Label(frame, text="Billing Cycle:").pack(anchor=tk.W)
        cycle_var = tk.StringVar(value="monthly")
        cycle_combo = ttk.Combobox(frame, textvariable=cycle_var,
                                   values=["weekly", "monthly", "yearly"])
        cycle_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Next Billing Date
        ttk.Label(frame, text="Next Billing Date (YYYY-MM-DD):").pack(anchor=tk.W)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(frame, textvariable=date_var).pack(fill=tk.X, pady=(0, 10))
        
        # Account
        ttk.Label(frame, text="Account (optional):").pack(anchor=tk.W)
        account_var = tk.StringVar()
        account_names = [""] + [a["name"] for a in self.accounts if a["is_active"]]
        account_combo = ttk.Combobox(frame, textvariable=account_var, values=account_names)
        account_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Notes
        ttk.Label(frame, text="Notes (optional):").pack(anchor=tk.W)
        notes_var = tk.StringVar()
        ttk.Entry(frame, textvariable=notes_var).pack(fill=tk.X, pady=(0, 20))
        
        def save():
            try:
                name = name_var.get().strip()
                amount = float(amount_var.get())
                billing_cycle = cycle_var.get()
                next_billing_date = datetime.strptime(date_var.get(), "%Y-%m-%d")
                
                if not name:
                    messagebox.showerror("Error", "Please enter a subscription name")
                    return
                
                account_id = None
                if account_var.get():
                    for a in self.accounts:
                        if a["name"] == account_var.get():
                            account_id = a["id"]
                            break
                
                notes = notes_var.get().strip() or None
                
                self.api.create_subscription(
                    name=name,
                    amount=amount,
                    billing_cycle=billing_cycle,
                    next_billing_date=next_billing_date,
                    account_id=account_id,
                    notes=notes
                )
                
                dialog.destroy()
                self._refresh_subscriptions_list()
                self.status_var.set("Subscription added successfully")
                
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(frame, text="Save Subscription", command=save).pack(fill=tk.X)
    
    # Context menus
    def _show_transaction_context_menu(self, event):
        """Show context menu for transactions."""
        item = self.trans_tree.identify_row(event.y)
        if item:
            self.trans_tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Delete Transaction", 
                           command=lambda: self._delete_transaction(int(item)))
            menu.post(event.x_root, event.y_root)
    
    def _show_account_context_menu(self, event):
        """Show context menu for accounts."""
        item = self.accounts_tree.identify_row(event.y)
        if item:
            self.accounts_tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Delete Account",
                           command=lambda: self._delete_account(int(item)))
            menu.post(event.x_root, event.y_root)
    
    def _show_subscription_context_menu(self, event):
        """Show context menu for subscriptions."""
        item = self.subs_tree.identify_row(event.y)
        if item:
            self.subs_tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Mark as Paid",
                           command=lambda: self._mark_subscription_paid(int(item)))
            menu.add_command(label="Delete Subscription",
                           command=lambda: self._delete_subscription(int(item)))
            menu.post(event.x_root, event.y_root)
    
    def _delete_transaction(self, trans_id: int):
        """Delete a transaction."""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?"):
            try:
                self.api.delete_transaction(trans_id)
                self._refresh_all_data()
                self.status_var.set("Transaction deleted")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _delete_account(self, account_id: int):
        """Delete an account."""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this account?"):
            try:
                self.api.delete_account(account_id)
                self._refresh_all_data()
                self.status_var.set("Account deleted")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _delete_subscription(self, sub_id: int):
        """Delete a subscription."""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this subscription?"):
            try:
                self.api.delete_subscription(sub_id)
                self._refresh_subscriptions_list()
                self.status_var.set("Subscription deleted")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _mark_subscription_paid(self, sub_id: int):
        """Mark a subscription as paid."""
        try:
            self.api.mark_subscription_paid(sub_id)
            self._refresh_subscriptions_list()
            self.status_var.set("Subscription marked as paid")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # Menu actions
    def _show_settings(self):
        """Show settings dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="API Server URL:").pack(anchor=tk.W)
        url_var = tk.StringVar(value=self.api.base_url)
        ttk.Entry(frame, textvariable=url_var).pack(fill=tk.X, pady=(0, 20))
        
        def save():
            self.api = APIClient(url_var.get())
            dialog.destroy()
            self._initial_load()
        
        ttk.Button(frame, text="Save", command=save).pack(fill=tk.X)
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About", 
                          "Transaction Tracker\n\n"
                          "A personal finance tracking application.\n\n"
                          "Version 1.0.0")


def main():
    """Application entry point."""
    root = tk.Tk()
    app = TransactionTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
