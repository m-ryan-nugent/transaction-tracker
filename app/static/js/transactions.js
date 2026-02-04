/**
 * Transactions Page JavaScript
 * 
 * Handles transaction CRUD operations and UI interactions.
 */

// State
let transactions = [];
let accounts = [];
let categories = [];
let editingTransactionId = null;
let currentTransactionType = 'expense';

// Pagination state
let currentPage = 1;
let totalTransactions = 0;
const PAGE_SIZE = 50;

// DOM Elements
const modal = document.getElementById('transaction-modal');
const deleteModal = document.getElementById('delete-modal');
const transactionForm = document.getElementById('transaction-form');

// -----------------------------------------------------------------------------
// Initialization
// -----------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([
        loadAccounts(),
        loadCategories(),
    ]);
    await loadTransactions();
    setupEventListeners();
    
    // Set default date to today
    document.getElementById('tx-date').value = new Date().toISOString().split('T')[0];
    
    // Re-run feather icons
    feather.replace();
});

function setupEventListeners() {
    // Add transaction button
    document.getElementById('add-transaction-btn').addEventListener('click', () => openTransactionModal());
    
    // Modal controls
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-cancel').addEventListener('click', closeModal);
    
    // Transaction type tabs
    document.querySelectorAll('.type-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTransactionType(tab.dataset.type));
    });
    
    // Form submit
    transactionForm.addEventListener('submit', handleFormSubmit);
    
    // Delete modal controls
    document.getElementById('delete-modal-close').addEventListener('click', closeDeleteModal);
    document.getElementById('delete-cancel').addEventListener('click', closeDeleteModal);
    document.getElementById('delete-confirm').addEventListener('click', confirmDelete);
    
    // Close modals on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) closeDeleteModal();
    });
    
    // Filters
    document.getElementById('filter-account').addEventListener('change', () => loadTransactions());
    document.getElementById('filter-category').addEventListener('change', () => loadTransactions());
    document.getElementById('filter-start-date').addEventListener('change', () => loadTransactions());
    document.getElementById('filter-end-date').addEventListener('change', () => loadTransactions());
    
    // Debounced search
    let searchTimeout;
    document.getElementById('filter-search').addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => loadTransactions(), 300);
    });
    
    document.getElementById('clear-filters-btn').addEventListener('click', clearFilters);
    
    // Pagination
    document.getElementById('prev-page').addEventListener('click', () => changePage(-1));
    document.getElementById('next-page').addEventListener('click', () => changePage(1));
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', async () => {
        await api.post('/auth/logout');
        window.location.href = '/login';
    });
}

// -----------------------------------------------------------------------------
// Data Loading
// -----------------------------------------------------------------------------

async function loadAccounts() {
    try {
        const response = await api.get('/accounts?is_active=true');
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to load accounts');
        }
        
        const data = await response.json();
        accounts = data.accounts;
        
        populateAccountSelects();
    } catch (error) {
        console.error('Error loading accounts:', error);
    }
}

async function loadCategories() {
    try {
        const response = await api.get('/categories?is_active=true');
        if (!response.ok) throw new Error('Failed to load categories');
        
        const data = await response.json();
        categories = data.categories;
        
        populateCategorySelects();
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadTransactions() {
    try {
        const params = new URLSearchParams();
        
        const accountId = document.getElementById('filter-account').value;
        const categoryId = document.getElementById('filter-category').value;
        const startDate = document.getElementById('filter-start-date').value;
        const endDate = document.getElementById('filter-end-date').value;
        const search = document.getElementById('filter-search').value;
        
        if (accountId) params.append('account_id', accountId);
        if (categoryId) params.append('category_id', categoryId);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (search) params.append('search', search);
        
        params.append('limit', PAGE_SIZE);
        params.append('offset', (currentPage - 1) * PAGE_SIZE);
        
        const response = await api.get(`/transactions?${params}`);
        if (!response.ok) throw new Error('Failed to load transactions');
        
        const data = await response.json();
        transactions = data.transactions;
        totalTransactions = data.total;
        
        renderTransactions();
        updatePagination();
    } catch (error) {
        console.error('Error loading transactions:', error);
        showToast('Failed to load transactions', 'danger');
    }
}

// -----------------------------------------------------------------------------
// Rendering
// -----------------------------------------------------------------------------

function populateAccountSelects() {
    const filterSelect = document.getElementById('filter-account');
    const txSelect = document.getElementById('tx-account');
    const transferSelect = document.getElementById('tx-transfer-to');
    
    const options = accounts.map(a => 
        `<option value="${a.id}">${a.name}</option>`
    ).join('');
    
    filterSelect.innerHTML = '<option value="">All Accounts</option>' + options;
    txSelect.innerHTML = '<option value="">Select account...</option>' + options;
    transferSelect.innerHTML = '<option value="">Select destination...</option>' + options;
}

function populateCategorySelects() {
    const filterSelect = document.getElementById('filter-category');
    const txSelect = document.getElementById('tx-category');
    
    // Group categories by type
    const grouped = {
        income: categories.filter(c => c.type === 'income'),
        expense: categories.filter(c => c.type === 'expense'),
        transfer: categories.filter(c => c.type === 'transfer'),
    };
    
    // Filter select - all categories
    let filterHtml = '<option value="">All Categories</option>';
    for (const [type, cats] of Object.entries(grouped)) {
        if (cats.length === 0) continue;
        filterHtml += `<optgroup label="${type.charAt(0).toUpperCase() + type.slice(1)}">`;
        filterHtml += cats.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        filterHtml += '</optgroup>';
    }
    filterSelect.innerHTML = filterHtml;
    
    // Transaction select - will be updated based on transaction type
    updateCategorySelect();
}

function updateCategorySelect() {
    const txSelect = document.getElementById('tx-category');
    const relevantCategories = categories.filter(c => c.type === currentTransactionType);
    
    let html = '<option value="">Select category...</option>';
    html += relevantCategories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    txSelect.innerHTML = html;
}

function renderTransactions() {
    const container = document.getElementById('transactions-list');
    document.getElementById('transaction-count').textContent = totalTransactions;
    
    if (transactions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon"><i data-feather="inbox" style="width: 48px; height: 48px;"></i></div>
                <div class="empty-state-title">No transactions found</div>
                <div class="empty-state-text">Try adjusting your filters or add a new transaction.</div>
                <button class="btn btn-primary" onclick="openTransactionModal()">Add Transaction</button>
            </div>
        `;
        feather.replace();
        return;
    }
    
    let html = '';
    
    for (const tx of transactions) {
        const isExpense = tx.amount < 0;
        const amountClass = isExpense ? 'negative' : 'positive';
        const amountPrefix = isExpense ? '' : '+';
        
        const payeeOrDesc = tx.payee || tx.description || 'No description';
        const categoryBadge = tx.category_name 
            ? `<span class="badge">${tx.category_name}</span>` 
            : '';
        
        html += `
            <div class="transaction-row" data-id="${tx.id}">
                <div class="transaction-date">${formatDate(tx.date)}</div>
                <div class="transaction-details">
                    <div class="transaction-payee">${escapeHtml(payeeOrDesc)}</div>
                    <div class="transaction-meta">
                        ${categoryBadge}
                        <span>${tx.account_name || 'Unknown Account'}</span>
                        ${tx.description && tx.payee ? `<span>${escapeHtml(tx.description)}</span>` : ''}
                    </div>
                </div>
                <div class="transaction-amount currency ${amountClass}">
                    ${amountPrefix}${formatCurrency(Math.abs(tx.amount))}
                </div>
                <div class="transaction-actions">
                    <button class="btn btn-ghost btn-sm" onclick="editTransaction(${tx.id})">
                        <i data-feather="edit-2" class="icon-sm"></i>
                    </button>
                    <button class="btn btn-ghost btn-sm text-danger" onclick="deleteTransaction(${tx.id})">
                        <i data-feather="trash-2" class="icon-sm"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
    feather.replace();
}

function updatePagination() {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(totalTransactions / PAGE_SIZE);
    
    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }
    
    pagination.style.display = 'flex';
    
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= totalPages;
    document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages}`;
}

function changePage(delta) {
    currentPage += delta;
    loadTransactions();
}

function clearFilters() {
    document.getElementById('filter-account').value = '';
    document.getElementById('filter-category').value = '';
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    document.getElementById('filter-search').value = '';
    currentPage = 1;
    loadTransactions();
}

// -----------------------------------------------------------------------------
// Modal Handling
// -----------------------------------------------------------------------------

function openTransactionModal(transactionId = null) {
    editingTransactionId = transactionId;
    const isEdit = transactionId !== null;
    
    // Reset form
    transactionForm.reset();
    document.getElementById('tx-date').value = new Date().toISOString().split('T')[0];
    
    // Update modal title
    document.getElementById('modal-title').textContent = isEdit ? 'Edit Transaction' : 'Add Transaction';
    document.getElementById('modal-submit').textContent = isEdit ? 'Update' : 'Save';
    
    if (isEdit) {
        const tx = transactions.find(t => t.id === transactionId);
        if (tx) {
            populateForm(tx);
        }
    } else {
        switchTransactionType('expense');
    }
    
    // Show modal
    modal.classList.add('active');
}

function closeModal() {
    modal.classList.remove('active');
    editingTransactionId = null;
    transactionForm.reset();
}

function switchTransactionType(type) {
    currentTransactionType = type;
    
    // Update tabs
    document.querySelectorAll('.type-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.type === type);
    });
    
    // Show/hide transfer fields
    const transferGroup = document.getElementById('transfer-to-group');
    const categoryGroup = document.getElementById('category-group');
    
    if (type === 'transfer') {
        transferGroup.style.display = 'block';
        categoryGroup.style.display = 'none';
    } else {
        transferGroup.style.display = 'none';
        categoryGroup.style.display = 'block';
    }
    
    // Update category dropdown
    updateCategorySelect();
}

function populateForm(tx) {
    // Determine transaction type
    if (tx.transfer_to_account_id) {
        switchTransactionType('transfer');
        document.getElementById('tx-transfer-to').value = tx.transfer_to_account_id;
    } else if (tx.amount > 0) {
        switchTransactionType('income');
    } else {
        switchTransactionType('expense');
    }
    
    document.getElementById('tx-date').value = tx.date;
    document.getElementById('tx-amount').value = Math.abs(tx.amount);
    document.getElementById('tx-account').value = tx.account_id;
    document.getElementById('tx-category').value = tx.category_id || '';
    document.getElementById('tx-payee').value = tx.payee || '';
    document.getElementById('tx-description').value = tx.description || '';
    document.getElementById('tx-notes').value = tx.notes || '';
}

// -----------------------------------------------------------------------------
// Form Submission
// -----------------------------------------------------------------------------

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('modal-submit');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Saving...';
    
    try {
        const data = buildTransactionData();
        
        if (editingTransactionId) {
            // Update existing
            const response = await api.patch(`/transactions/${editingTransactionId}`, {
                date: data.date,
                amount: data.amount,
                description: data.description,
                payee: data.payee,
                notes: data.notes,
                category_id: data.category_id,
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update transaction');
            }
            
            showToast('Transaction updated', 'success');
        } else {
            // Create new
            const response = await api.post('/transactions', data);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create transaction');
            }
            
            showToast('Transaction added', 'success');
        }
        
        closeModal();
        await loadTransactions();
        
    } catch (error) {
        console.error('Error saving transaction:', error);
        showToast(error.message || 'Failed to save transaction', 'danger');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = editingTransactionId ? 'Update' : 'Save';
    }
}

function buildTransactionData() {
    let amount = parseFloat(document.getElementById('tx-amount').value);
    
    // Make amount negative for expenses
    if (currentTransactionType === 'expense' || currentTransactionType === 'transfer') {
        amount = -Math.abs(amount);
    } else {
        amount = Math.abs(amount);
    }
    
    const data = {
        date: document.getElementById('tx-date').value,
        amount: amount,
        account_id: parseInt(document.getElementById('tx-account').value),
        description: document.getElementById('tx-description').value || null,
        payee: document.getElementById('tx-payee').value || null,
        notes: document.getElementById('tx-notes').value || null,
        category_id: null,
        transfer_to_account_id: null,
    };
    
    if (currentTransactionType === 'transfer') {
        data.transfer_to_account_id = parseInt(document.getElementById('tx-transfer-to').value) || null;
    } else {
        data.category_id = parseInt(document.getElementById('tx-category').value) || null;
    }
    
    return data;
}

// -----------------------------------------------------------------------------
// Delete Handling
// -----------------------------------------------------------------------------

let deletingTransactionId = null;

function deleteTransaction(transactionId) {
    deletingTransactionId = transactionId;
    deleteModal.classList.add('active');
}

function closeDeleteModal() {
    deleteModal.classList.remove('active');
    deletingTransactionId = null;
}

async function confirmDelete() {
    if (!deletingTransactionId) return;
    
    const deleteBtn = document.getElementById('delete-confirm');
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<span class="spinner"></span> Deleting...';
    
    try {
        const response = await api.delete(`/transactions/${deletingTransactionId}`);
        
        if (!response.ok) {
            throw new Error('Failed to delete transaction');
        }
        
        showToast('Transaction deleted', 'success');
        closeDeleteModal();
        await loadTransactions();
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showToast('Failed to delete transaction', 'danger');
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.textContent = 'Delete';
    }
}

// Make functions available globally
window.openTransactionModal = openTransactionModal;
window.editTransaction = openTransactionModal;
window.deleteTransaction = deleteTransaction;

// -----------------------------------------------------------------------------
// Utilities
// -----------------------------------------------------------------------------

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
