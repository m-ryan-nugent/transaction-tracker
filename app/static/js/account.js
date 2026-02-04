/**
 * Accounts Page JavaScript
 * 
 * Handles account CRUD operations and UI interactions.
 */

let accounts = [];
let editingAccountId = null;

const modal = document.getElementById('account-modal');
const deleteModal = document.getElementById('delete-modal');
const accountForm = document.getElementById('account-form');
const accountTypeSelect = document.getElementById('account-type');

const typeFields = {
    bank: document.getElementById('bank-fields'),
    credit_card: document.getElementById('credit-card-fields'),
    loan: document.getElementById('loan-fields'),
    investment: document.getElementById('investment-fields'),
};


document.addEventListener('DOMContentLoaded', () => {
    loadAccounts();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('add-account-btn').addEventListener('click', () => openModal());
    
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-cancel').addEventListener('click', closeModal);

    accountTypeSelect.addEventListener('change', handleTypeChange);
    
    accountForm.addEventListener('submit', handleFormSubmit);
    
    document.getElementById('delete-modal-close').addEventListener('click', closeDeleteModal);
    document.getElementById('delete-cancel').addEventListener('click', closeDeleteModal);
    document.getElementById('delete-confirm').addEventListener('click', confirmDelete);
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) closeDeleteModal();
    });
    
    document.getElementById('logout-btn').addEventListener('click', async () => {
        await api.post('/auth/logout');
        window.location.href = '/login';
    });
}

async function loadAccounts() {
    try {
        const response = await api.get('/accounts');
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to load accounts');
        }
        
        const data = await response.json();
        accounts = data.accounts;
        renderAccounts();
    } catch (error) {
        console.error('Error loading accounts:', error);
        showToast('Failed to load accounts', 'danger');
    }
}


function renderAccounts() {
    const grouped = {
        bank: [],
        credit_card: [],
        loan: [],
        investment: [],
    };
    
    accounts.forEach(account => {
        if (grouped[account.account_type]) {
            grouped[account.account_type].push(account);
        }
    });
    
    renderAccountGroup('bank-accounts-list', grouped.bank, 'bank');
    renderAccountGroup('credit-card-accounts-list', grouped.credit_card, 'credit_card');
    renderAccountGroup('loan-accounts-list', grouped.loan, 'loan');
    renderAccountGroup('investment-accounts-list', grouped.investment, 'investment');
}

function renderAccountGroup(containerId, accounts, type) {
    const container = document.getElementById(containerId);
    
    if (accounts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p class="text-muted">No ${type.replace('_', ' ')}s yet</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="table-wrapper"><table class="table"><thead><tr>';
    html += '<th>Name</th><th>Institution</th>';
    
    if (type === 'credit_card') {
        html += '<th>Balance</th><th>Limit</th><th>Available</th>';
    } else if (type === 'loan') {
        html += '<th>Balance</th><th>Original</th><th>Paid</th>';
    } else {
        html += '<th>Balance</th>';
    }
    
    html += '<th>Actions</th></tr></thead><tbody>';
    
    accounts.forEach(account => {
        html += `<tr data-id="${account.id}">`;
        html += `<td><strong>${escapeHtml(account.name)}</strong></td>`;
        html += `<td>${escapeHtml(account.institution || '-')}</td>`;
        
        const balanceClass = (type === 'credit_card' || type === 'loan') ? 'negative' : 'positive';
        
        if (type === 'credit_card') {
            html += `<td class="currency ${balanceClass}">${formatCurrency(account.current_balance)}</td>`;
            html += `<td class="currency">${formatCurrency(account.credit_limit)}</td>`;
            html += `<td class="currency positive">${formatCurrency(account.available_credit)}</td>`;
        } else if (type === 'loan') {
            html += `<td class="currency ${balanceClass}">${formatCurrency(account.current_balance)}</td>`;
            html += `<td class="currency">${formatCurrency(account.original_amount)}</td>`;
            html += `<td class="currency positive">${formatCurrency(account.loan_paid)}</td>`;
        } else {
            html += `<td class="currency ${balanceClass}">${formatCurrency(account.current_balance)}</td>`;
        }
        
        html += `
            <td>
                <button class="btn btn-ghost btn-sm" onclick="editAccount(${account.id})">Edit</button>
                <button class="btn btn-ghost btn-sm text-danger" onclick="deleteAccount(${account.id})">Delete</button>
            </td>
        `;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function openModal(accountId = null) {
    editingAccountId = accountId;
    const isEdit = accountId !== null;
    
    accountForm.reset();
    hideAllTypeFields();
    
    document.getElementById('modal-title').textContent = isEdit ? 'Edit Account' : 'Add Account';
    document.getElementById('modal-submit').textContent = isEdit ? 'Update Account' : 'Save Account';
    
    const typeGroup = document.getElementById('account-type-group');
    typeGroup.style.display = isEdit ? 'none' : 'block';
    
    if (isEdit) {
        const account = accounts.find(a => a.id === accountId);
        if (account) {
            populateForm(account);
        }
    }
    
    modal.classList.add('active');
}

function closeModal() {
    modal.classList.remove('active');
    editingAccountId = null;
    accountForm.reset();
    hideAllTypeFields();
}

function handleTypeChange() {
    hideAllTypeFields();
    const type = accountTypeSelect.value;
    
    if (type && typeFields[type]) {
        typeFields[type].style.display = 'block';
    }
}

function hideAllTypeFields() {
    Object.values(typeFields).forEach(el => {
        el.style.display = 'none';
    });
}

function populateForm(account) {
    document.getElementById('account-name').value = account.name;
    document.getElementById('account-institution').value = account.institution || '';
    document.getElementById('account-notes').value = account.notes || '';
    
    const type = account.account_type;
    if (typeFields[type]) {
        typeFields[type].style.display = 'block';
    }
    
    switch (type) {
        case 'bank':
            document.getElementById('bank-balance').value = account.current_balance;
            break;
        case 'credit_card':
            document.getElementById('cc-limit').value = account.credit_limit;
            document.getElementById('cc-balance').value = account.current_balance;
            document.getElementById('cc-apr').value = account.interest_rate || '';
            break;
        case 'loan':
            document.getElementById('loan-original').value = account.original_amount;
            document.getElementById('loan-balance').value = account.current_balance;
            document.getElementById('loan-rate').value = account.interest_rate;
            document.getElementById('loan-term').value = account.loan_term_months;
            document.getElementById('loan-start').value = account.loan_start_date || '';
            break;
        case 'investment':
            document.getElementById('invest-balance').value = account.current_balance;
            document.getElementById('invest-initial').value = account.initial_investment || '';
            break;
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('modal-submit');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Saving...';
    
    try {
        let data;
        let endpoint;
        
        if (editingAccountId) {
            data = buildUpdateData();
            endpoint = `/accounts/${editingAccountId}`;
            
            const response = await api.patch(endpoint, data);
            
            if (!response.ok) {
                throw new Error('Failed to update account');
            }
            
            showToast('Account updated successfully', 'success');
        } else {
            const type = accountTypeSelect.value;
            data = buildCreateData(type);
            endpoint = `/accounts/${type.replace('_', '-')}`;
            
            const response = await api.post(endpoint, data);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create account');
            }
            
            showToast('Account created successfully', 'success');
        }
        
        closeModal();
        await loadAccounts();
    } catch (error) {
        console.error('Error saving account:', error);
        showToast(error.message || 'Failed to save account', 'danger');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = editingAccountId ? 'Update Account' : 'Save Account';
    }
}

function buildCreateData(type) {
    const base = {
        name: document.getElementById('account-name').value,
        institution: document.getElementById('account-institution').value || null,
        notes: document.getElementById('account-notes').value || null,
    };
    
    switch (type) {
        case 'bank':
            return {
                ...base,
                current_balance: parseFloat(document.getElementById('bank-balance').value) || 0,
            };
        case 'credit_card':
            return {
                ...base,
                credit_limit: parseFloat(document.getElementById('cc-limit').value),
                current_balance: parseFloat(document.getElementById('cc-balance').value) || 0,
                interest_rate: parseFloat(document.getElementById('cc-apr').value) || null,
            };
        case 'loan':
            return {
                ...base,
                original_amount: parseFloat(document.getElementById('loan-original').value),
                current_balance: parseFloat(document.getElementById('loan-balance').value),
                interest_rate: parseFloat(document.getElementById('loan-rate').value),
                loan_term_months: parseInt(document.getElementById('loan-term').value),
                loan_start_date: document.getElementById('loan-start').value,
            };
        case 'investment':
            return {
                ...base,
                current_balance: parseFloat(document.getElementById('invest-balance').value) || 0,
                initial_investment: parseFloat(document.getElementById('invest-initial').value) || null,
            };
        default:
            return base;
    }
}

function buildUpdateData() {
    const account = accounts.find(a => a.id === editingAccountId);
    if (!account) return {};
    
    const data = {
        name: document.getElementById('account-name').value,
        institution: document.getElementById('account-institution').value || null,
        notes: document.getElementById('account-notes').value || null,
    };
    
    switch (account.account_type) {
        case 'bank':
            data.current_balance = parseFloat(document.getElementById('bank-balance').value) || 0;
            break;
        case 'credit_card':
            data.credit_limit = parseFloat(document.getElementById('cc-limit').value);
            data.current_balance = parseFloat(document.getElementById('cc-balance').value) || 0;
            data.interest_rate = parseFloat(document.getElementById('cc-apr').value) || null;
            break;
        case 'loan':
            data.original_amount = parseFloat(document.getElementById('loan-original').value);
            data.current_balance = parseFloat(document.getElementById('loan-balance').value);
            data.interest_rate = parseFloat(document.getElementById('loan-rate').value);
            data.loan_term_months = parseInt(document.getElementById('loan-term').value);
            data.loan_start_date = document.getElementById('loan-start').value;
            break;
        case 'investment':
            data.current_balance = parseFloat(document.getElementById('invest-balance').value) || 0;
            data.initial_investment = parseFloat(document.getElementById('invest-initial').value) || null;
            break;
    }
    
    return data;
}

let deletingAccountId = null;

function deleteAccount(accountId) {
    const account = accounts.find(a => a.id === accountId);
    if (!account) return;
    
    deletingAccountId = accountId;
    document.getElementById('delete-account-name').textContent = account.name;
    deleteModal.classList.add('active');
}

function closeDeleteModal() {
    deleteModal.classList.remove('active');
    deletingAccountId = null;
}

async function confirmDelete() {
    if (!deletingAccountId) return;
    
    const deleteBtn = document.getElementById('delete-confirm');
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<span class="spinner"></span> Deleting...';
    
    try {
        const response = await api.delete(`/accounts/${deletingAccountId}`);
        
        if (!response.ok) {
            throw new Error('Failed to delete account');
        }
        
        showToast('Account deleted successfully', 'success');
        closeDeleteModal();
        await loadAccounts();
    } catch (error) {
        console.error('Error deleting account:', error);
        showToast('Failed to delete account', 'danger');
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.textContent = 'Delete';
    }
}

window.editAccount = openModal;
window.deleteAccount = deleteAccount;

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
