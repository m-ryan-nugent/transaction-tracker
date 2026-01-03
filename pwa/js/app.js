/**
 * Transaction Tracker PWA
 * Main JavaScript Application
 */

// ============== Configuration ==============
const DEFAULT_API_URL = 'http://localhost:8000';
let API_URL = localStorage.getItem('apiUrl') || DEFAULT_API_URL;

// ============== API Client ==============
const api = {
    async request(method, endpoint, data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(`${API_URL}${endpoint}`, options);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            if (response.status === 204) {
                return null;
            }
            
            return response.json();
        } catch (error) {
            if (error.name === 'TypeError') {
                throw new Error('Could not connect to server. Check settings.');
            }
            throw error;
        }
    },
    
    // Accounts
    getAccounts: () => api.request('GET', '/accounts/'),
    createAccount: (data) => api.request('POST', '/accounts/', data),
    deleteAccount: (id) => api.request('DELETE', `/accounts/${id}`),
    
    // Transactions
    getTransactions: (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return api.request('GET', `/transactions/?${query}`);
    },
    createTransaction: (data) => api.request('POST', '/transactions/', data),
    deleteTransaction: (id) => api.request('DELETE', `/transactions/${id}`),
    
    // Categories
    getCategories: () => api.request('GET', '/categories/'),
    
    // Subscriptions
    getSubscriptions: () => api.request('GET', '/subscriptions/'),
    createSubscription: (data) => api.request('POST', '/subscriptions/', data),
    deleteSubscription: (id) => api.request('DELETE', `/subscriptions/${id}`),
    markSubscriptionPaid: (id) => api.request('POST', `/subscriptions/${id}/mark-paid`),
    
    // Dashboard
    getMonthlySummary: () => api.request('GET', '/dashboard/summary'),
    getCreditCardOverview: () => api.request('GET', '/dashboard/credit-cards'),
    getRecentTransactions: () => api.request('GET', '/dashboard/recent-transactions?limit=10')
};

// ============== State ==============
let accounts = [];
let categories = [];
let transactions = [];
let subscriptions = [];

// ============== DOM Elements ==============
const elements = {
    // Tabs
    navButtons: document.querySelectorAll('.nav-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Dashboard
    totalIncome: document.getElementById('totalIncome'),
    totalExpenses: document.getElementById('totalExpenses'),
    totalNet: document.getElementById('totalNet'),
    creditCardList: document.getElementById('creditCardList'),
    recentTransactions: document.getElementById('recentTransactions'),
    
    // Transactions
    transactionList: document.getElementById('transactionList'),
    transAccountFilter: document.getElementById('transAccountFilter'),
    transTypeFilter: document.getElementById('transTypeFilter'),
    addTransactionBtn: document.getElementById('addTransactionBtn'),
    
    // Accounts
    accountList: document.getElementById('accountList'),
    addAccountBtn: document.getElementById('addAccountBtn'),
    
    // Subscriptions
    subscriptionList: document.getElementById('subscriptionList'),
    addSubscriptionBtn: document.getElementById('addSubscriptionBtn'),
    
    // Modals
    transactionModal: document.getElementById('transactionModal'),
    accountModal: document.getElementById('accountModal'),
    subscriptionModal: document.getElementById('subscriptionModal'),
    settingsModal: document.getElementById('settingsModal'),
    
    // Forms
    transactionForm: document.getElementById('transactionForm'),
    accountForm: document.getElementById('accountForm'),
    subscriptionForm: document.getElementById('subscriptionForm'),
    settingsForm: document.getElementById('settingsForm'),
    
    // Settings
    settingsBtn: document.getElementById('settingsBtn'),
    apiUrl: document.getElementById('apiUrl'),
    
    // Toast
    toast: document.getElementById('toast')
};

// ============== Utilities ==============
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function showToast(message, duration = 3000) {
    elements.toast.textContent = message;
    elements.toast.classList.add('show');
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, duration);
}

function getTodayDate() {
    return new Date().toISOString().split('T')[0];
}

// ============== Navigation ==============
function switchTab(tabName) {
    elements.navButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });
    
    // Refresh data when switching tabs
    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'transactions') loadTransactions();
    if (tabName === 'accounts') loadAccounts();
    if (tabName === 'subscriptions') loadSubscriptions();
}

// ============== Modal Management ==============
function openModal(modal) {
    modal.classList.add('active');
}

function closeModal(modal) {
    modal.classList.remove('active');
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

// ============== Data Loading ==============
async function loadInitialData() {
    try {
        [accounts, categories] = await Promise.all([
            api.getAccounts(),
            api.getCategories()
        ]);
        
        populateAccountSelects();
        populateCategorySelect();
        
        loadDashboard();
        showToast('Connected to server');
    } catch (error) {
        showToast(error.message);
    }
}

function populateAccountSelects() {
    const selects = [
        elements.transAccountFilter,
        document.getElementById('transAccount'),
        document.getElementById('subAccount')
    ];
    
    selects.forEach(select => {
        if (!select) return;
        
        const isFilter = select.id.includes('Filter');
        select.innerHTML = isFilter ? '<option value="">All Accounts</option>' : '';
        
        if (select.id === 'subAccount') {
            select.innerHTML = '<option value="">None</option>';
        }
        
        accounts.filter(a => a.is_active).forEach(account => {
            const option = document.createElement('option');
            option.value = account.id;
            option.textContent = account.name;
            select.appendChild(option);
        });
    });
}

function populateCategorySelect() {
    const select = document.getElementById('transCategory');
    if (!select) return;
    
    select.innerHTML = '<option value="">No Category</option>';
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        select.appendChild(option);
    });
}

// ============== Dashboard ==============
async function loadDashboard() {
    try {
        const [summary, creditCards, recent] = await Promise.all([
            api.getMonthlySummary(),
            api.getCreditCardOverview(),
            api.getRecentTransactions()
        ]);
        
        // Update summary cards
        elements.totalIncome.textContent = formatCurrency(summary.total_income);
        elements.totalExpenses.textContent = formatCurrency(summary.total_expenses);
        
        const net = summary.net;
        elements.totalNet.textContent = (net < 0 ? '-' : '') + formatCurrency(Math.abs(net));
        elements.totalNet.parentElement.parentElement.classList.toggle('expense-card', net < 0);
        
        // Update credit cards
        elements.creditCardList.innerHTML = creditCards.length ? '' : 
            '<div class="empty-state"><p>No credit cards added yet</p></div>';
        
        creditCards.forEach(card => {
            const util = card.utilization_percent || 0;
            let progressClass = '';
            if (util > 90) progressClass = 'danger';
            else if (util > 70) progressClass = 'warning';
            
            elements.creditCardList.innerHTML += `
                <div class="credit-card-item">
                    <h3>${card.name}</h3>
                    <div class="progress-bar">
                        <div class="progress-fill ${progressClass}" style="width: ${Math.min(util, 100)}%"></div>
                    </div>
                    <div class="credit-card-stats">
                        <span>Spent: ${formatCurrency(card.spent_this_month)}</span>
                        <span>Limit: ${formatCurrency(card.credit_limit)}</span>
                    </div>
                </div>
            `;
        });
        
        // Update recent transactions
        elements.recentTransactions.innerHTML = recent.length ? '' :
            '<div class="empty-state"><p>No transactions yet</p></div>';
        
        recent.forEach(trans => {
            const amountClass = trans.is_income ? 'income' : 'expense';
            const sign = trans.is_income ? '+' : '-';
            
            elements.recentTransactions.innerHTML += `
                <div class="transaction-item">
                    <div class="transaction-info">
                        <div class="transaction-description">${trans.description}</div>
                        <div class="transaction-meta">${formatDate(trans.date)}</div>
                    </div>
                    <div class="transaction-amount ${amountClass}">
                        ${sign}${formatCurrency(trans.amount)}
                    </div>
                </div>
            `;
        });
        
    } catch (error) {
        showToast(error.message);
    }
}

// ============== Transactions ==============
async function loadTransactions() {
    try {
        const params = { limit: 100 };
        
        const accountFilter = elements.transAccountFilter.value;
        if (accountFilter) {
            params.account_id = accountFilter;
        }
        
        const typeFilter = elements.transTypeFilter.value;
        if (typeFilter === 'income') {
            params.is_income = true;
        } else if (typeFilter === 'expense') {
            params.is_income = false;
        }
        
        transactions = await api.getTransactions(params);
        renderTransactions();
        
    } catch (error) {
        showToast(error.message);
    }
}

function renderTransactions() {
    elements.transactionList.innerHTML = transactions.length ? '' :
        '<div class="empty-state"><p>No transactions found</p><p>Add your first transaction!</p></div>';
    
    transactions.forEach(trans => {
        const amountClass = trans.is_income ? 'income' : 'expense';
        const sign = trans.is_income ? '+' : '-';
        const category = trans.category?.name || 'Uncategorized';
        const account = trans.account?.name || 'Unknown';
        
        elements.transactionList.innerHTML += `
            <div class="transaction-item" data-id="${trans.id}">
                <div class="transaction-info">
                    <div class="transaction-description">${trans.description}</div>
                    <div class="transaction-meta">${formatDate(trans.date)} • ${category} • ${account}</div>
                </div>
                <div class="transaction-amount ${amountClass}">
                    ${sign}${formatCurrency(trans.amount)}
                </div>
                <div class="item-actions">
                    <button class="delete-btn" onclick="deleteTransaction(${trans.id})">🗑️</button>
                </div>
            </div>
        `;
    });
}

async function createTransaction(e) {
    e.preventDefault();
    
    const data = {
        amount: parseFloat(document.getElementById('transAmount').value),
        description: document.getElementById('transDescription').value,
        date: document.getElementById('transDate').value + 'T12:00:00',
        account_id: parseInt(document.getElementById('transAccount').value),
        is_income: document.getElementById('transIsIncome').checked
    };
    
    const categoryId = document.getElementById('transCategory').value;
    if (categoryId) {
        data.category_id = parseInt(categoryId);
    }
    
    const notes = document.getElementById('transNotes').value;
    if (notes) {
        data.notes = notes;
    }
    
    try {
        await api.createTransaction(data);
        closeModal(elements.transactionModal);
        elements.transactionForm.reset();
        document.getElementById('transDate').value = getTodayDate();
        loadTransactions();
        showToast('Transaction added!');
    } catch (error) {
        showToast(error.message);
    }
}

async function deleteTransaction(id) {
    if (!confirm('Delete this transaction?')) return;
    
    try {
        await api.deleteTransaction(id);
        loadTransactions();
        showToast('Transaction deleted');
    } catch (error) {
        showToast(error.message);
    }
}

// ============== Accounts ==============
async function loadAccounts() {
    try {
        accounts = await api.getAccounts();
        renderAccounts();
        populateAccountSelects();
    } catch (error) {
        showToast(error.message);
    }
}

function renderAccounts() {
    elements.accountList.innerHTML = accounts.length ? '' :
        '<div class="empty-state"><p>No accounts added yet</p><p>Add your first account!</p></div>';
    
    accounts.filter(a => a.is_active).forEach(account => {
        const type = account.account_type.replace('_', ' ');
        const limitText = account.credit_limit ? 
            `Limit: ${formatCurrency(account.credit_limit)}` : '';
        
        elements.accountList.innerHTML += `
            <div class="account-item" data-id="${account.id}">
                <div class="account-info">
                    <h3>${account.name}</h3>
                    <div class="account-type">${type}</div>
                </div>
                <div class="account-balance">
                    <div class="balance">${formatCurrency(account.current_balance)}</div>
                    <div class="limit">${limitText}</div>
                </div>
                <div class="item-actions">
                    <button class="delete-btn" onclick="deleteAccount(${account.id})">🗑️</button>
                </div>
            </div>
        `;
    });
}

async function createAccount(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('accountName').value,
        account_type: document.getElementById('accountType').value,
        current_balance: parseFloat(document.getElementById('accountBalance').value) || 0
    };
    
    const creditLimit = document.getElementById('accountLimit').value;
    if (creditLimit) {
        data.credit_limit = parseFloat(creditLimit);
    }
    
    try {
        await api.createAccount(data);
        closeModal(elements.accountModal);
        elements.accountForm.reset();
        loadAccounts();
        showToast('Account added!');
    } catch (error) {
        showToast(error.message);
    }
}

async function deleteAccount(id) {
    if (!confirm('Delete this account?')) return;
    
    try {
        await api.deleteAccount(id);
        loadAccounts();
        showToast('Account deleted');
    } catch (error) {
        showToast(error.message);
    }
}

// ============== Subscriptions ==============
async function loadSubscriptions() {
    try {
        subscriptions = await api.getSubscriptions();
        renderSubscriptions();
    } catch (error) {
        showToast(error.message);
    }
}

function renderSubscriptions() {
    elements.subscriptionList.innerHTML = subscriptions.length ? '' :
        '<div class="empty-state"><p>No subscriptions added yet</p><p>Track your recurring payments!</p></div>';
    
    subscriptions.filter(s => s.is_active).forEach(sub => {
        const nextDate = formatDate(sub.next_billing_date);
        
        elements.subscriptionList.innerHTML += `
            <div class="subscription-item" data-id="${sub.id}">
                <div class="subscription-info">
                    <h3>${sub.name}</h3>
                    <div class="subscription-meta">${sub.billing_cycle}</div>
                </div>
                <div class="subscription-amount">
                    <div class="amount">${formatCurrency(sub.amount)}</div>
                    <div class="next-date">Next: ${nextDate}</div>
                </div>
                <div class="item-actions">
                    <button class="action-btn" onclick="markSubscriptionPaid(${sub.id})">Paid</button>
                    <button class="delete-btn" onclick="deleteSubscription(${sub.id})">🗑️</button>
                </div>
            </div>
        `;
    });
}

async function createSubscription(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('subName').value,
        amount: parseFloat(document.getElementById('subAmount').value),
        billing_cycle: document.getElementById('subCycle').value,
        next_billing_date: document.getElementById('subNextDate').value + 'T12:00:00'
    };
    
    const accountId = document.getElementById('subAccount').value;
    if (accountId) {
        data.account_id = parseInt(accountId);
    }
    
    const notes = document.getElementById('subNotes').value;
    if (notes) {
        data.notes = notes;
    }
    
    try {
        await api.createSubscription(data);
        closeModal(elements.subscriptionModal);
        elements.subscriptionForm.reset();
        document.getElementById('subNextDate').value = getTodayDate();
        loadSubscriptions();
        showToast('Subscription added!');
    } catch (error) {
        showToast(error.message);
    }
}

async function markSubscriptionPaid(id) {
    try {
        await api.markSubscriptionPaid(id);
        loadSubscriptions();
        showToast('Marked as paid!');
    } catch (error) {
        showToast(error.message);
    }
}

async function deleteSubscription(id) {
    if (!confirm('Delete this subscription?')) return;
    
    try {
        await api.deleteSubscription(id);
        loadSubscriptions();
        showToast('Subscription deleted');
    } catch (error) {
        showToast(error.message);
    }
}

// ============== Settings ==============
function saveSettings(e) {
    e.preventDefault();
    
    const newUrl = elements.apiUrl.value.trim();
    if (newUrl) {
        API_URL = newUrl;
        localStorage.setItem('apiUrl', API_URL);
    }
    
    closeModal(elements.settingsModal);
    loadInitialData();
}

// ============== Event Listeners ==============
function setupEventListeners() {
    // Navigation
    elements.navButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Add buttons
    elements.addTransactionBtn.addEventListener('click', () => {
        document.getElementById('transDate').value = getTodayDate();
        openModal(elements.transactionModal);
    });
    
    elements.addAccountBtn.addEventListener('click', () => {
        // Reset form and labels
        elements.accountForm.reset();
        document.getElementById('creditLimitGroup').style.display = 'none';
        document.getElementById('balanceLabel').textContent = 'Initial Balance';
        document.getElementById('balanceHint').textContent = '';
        openModal(elements.accountModal);
    });
    
    elements.addSubscriptionBtn.addEventListener('click', () => {
        document.getElementById('subNextDate').value = getTodayDate();
        openModal(elements.subscriptionModal);
    });
    
    elements.settingsBtn.addEventListener('click', () => {
        elements.apiUrl.value = API_URL;
        openModal(elements.settingsModal);
    });
    
    // Close buttons
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            closeAllModals();
        });
    });
    
    // Close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });
    
    // Forms
    elements.transactionForm.addEventListener('submit', createTransaction);
    elements.accountForm.addEventListener('submit', createAccount);
    elements.subscriptionForm.addEventListener('submit', createSubscription);
    elements.settingsForm.addEventListener('submit', saveSettings);
    
    // Filters
    elements.transAccountFilter.addEventListener('change', loadTransactions);
    elements.transTypeFilter.addEventListener('change', loadTransactions);
    
    // Account type change - show/hide credit limit and update balance label
    document.getElementById('accountType').addEventListener('change', (e) => {
        const isCreditCard = e.target.value === 'credit_card';
        const creditLimitGroup = document.getElementById('creditLimitGroup');
        const balanceLabel = document.getElementById('balanceLabel');
        const balanceHint = document.getElementById('balanceHint');
        
        creditLimitGroup.style.display = isCreditCard ? 'block' : 'none';
        
        if (isCreditCard) {
            balanceLabel.textContent = 'Current Amount Owed';
            balanceHint.textContent = 'How much you currently owe on this card';
        } else {
            balanceLabel.textContent = 'Initial Balance';
            balanceHint.textContent = '';
        }
    });
}

// ============== Service Worker Registration ==============
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('Service Worker registration failed:', err));
    });
}

// ============== Initialize App ==============
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadInitialData();
});

// Make delete functions globally available
window.deleteTransaction = deleteTransaction;
window.deleteAccount = deleteAccount;
window.deleteSubscription = deleteSubscription;
window.markSubscriptionPaid = markSubscriptionPaid;
