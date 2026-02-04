/**
 * Loans Page JavaScript
 */

let loans = [];
let accounts = [];
let editingLoanId = null;
let deletingLoanId = null;
let paymentLoanId = null;
let currentFilter = 'all';

const loansList = document.getElementById('loans-list');
const addLoanBtn = document.getElementById('add-loan-btn');
const loanModal = document.getElementById('loan-modal');
const loanForm = document.getElementById('loan-form');
const modalTitle = document.getElementById('modal-title');
const modalClose = document.getElementById('modal-close');
const modalCancel = document.getElementById('modal-cancel');
const paymentModal = document.getElementById('payment-modal');
const paymentForm = document.getElementById('payment-form');
const paymentModalClose = document.getElementById('payment-modal-close');
const paymentCancel = document.getElementById('payment-cancel');
const amortModal = document.getElementById('amortization-modal');
const amortModalClose = document.getElementById('amort-modal-close');
const amortClose = document.getElementById('amort-close');
const deleteModal = document.getElementById('delete-modal');
const deleteModalClose = document.getElementById('delete-modal-close');
const deleteCancel = document.getElementById('delete-cancel');
const deleteConfirm = document.getElementById('delete-confirm');
const logoutBtn = document.getElementById('logout-btn');

const activeCountEl = document.getElementById('active-count');
const totalBalanceEl = document.getElementById('total-balance');
const monthlyPaymentsEl = document.getElementById('monthly-payments');

document.addEventListener('DOMContentLoaded', () => {
    init();
    feather.replace();
});

async function init() {
    if (!getToken()) {
        window.location.href = '/login';
        return;
    }

    await Promise.all([
        loadLoans(),
        loadAccounts()
    ]);

    setupEventListeners();
}

function setupEventListeners() {
    addLoanBtn.addEventListener('click', () => openLoanModal());

    modalClose.addEventListener('click', closeLoanModal);
    modalCancel.addEventListener('click', closeLoanModal);
    loanModal.addEventListener('click', (e) => {
        if (e.target === loanModal) closeLoanModal();
    });

    loanForm.addEventListener('submit', handleLoanSubmit);

    paymentModalClose.addEventListener('click', closePaymentModal);
    paymentCancel.addEventListener('click', closePaymentModal);
    paymentModal.addEventListener('click', (e) => {
        if (e.target === paymentModal) closePaymentModal();
    });

    paymentForm.addEventListener('submit', handlePaymentSubmit);

    amortModalClose.addEventListener('click', closeAmortModal);
    amortClose.addEventListener('click', closeAmortModal);
    amortModal.addEventListener('click', (e) => {
        if (e.target === amortModal) closeAmortModal();
    });

    deleteModalClose.addEventListener('click', closeDeleteModal);
    deleteCancel.addEventListener('click', closeDeleteModal);
    deleteConfirm.addEventListener('click', confirmDelete);
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) closeDeleteModal();
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderLoans();
        });
    });

    logoutBtn.addEventListener('click', () => {
        logout();
        window.location.href = '/login';
    });
}

async function loadLoans() {
    try {
        const data = await apiRequest('/api/loans');
        loans = data.loans;
        updateSummary(data);
        renderLoans();
    } catch (error) {
        console.error('Failed to load loans:', error);
        showNotification('Failed to load loans', 'error');
    }
}

async function loadAccounts() {
    try {
        const data = await apiRequest('/api/accounts');
        accounts = data.accounts;
        populateAccountSelect();
    } catch (error) {
        console.error('Failed to load accounts:', error);
    }
}

async function createLoan(data) {
    return await apiRequest('/api/loans', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function updateLoan(id, data) {
    return await apiRequest(`/api/loans/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    });
}

async function deleteLoan(id) {
    return await apiRequest(`/api/loans/${id}`, {
        method: 'DELETE'
    });
}

async function getAmortizationSchedule(id) {
    return await apiRequest(`/api/loans/${id}/amortization`);
}

async function recordPayment(loanId, data) {
    return await apiRequest(`/api/loans/${loanId}/payments`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

function renderLoans() {
    let filteredLoans = loans;

    if (currentFilter === 'active') {
        filteredLoans = loans.filter(l => l.is_active);
    } else if (currentFilter === 'paid') {
        filteredLoans = loans.filter(l => !l.is_active);
    }

    if (filteredLoans.length === 0) {
        loansList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon"><i data-feather="file-text" style="width: 48px; height: 48px;"></i></div>
                <div class="empty-state-title">${currentFilter === 'all' ? 'No loans yet' : `No ${currentFilter} loans`}</div>
                <div class="empty-state-text">${currentFilter === 'all' ? 'Track your loans and see amortization schedules.' : ''}</div>
                ${currentFilter === 'all' ? '<button class="btn btn-primary" onclick="openLoanModal()">Add Loan</button>' : ''}
            </div>
        `;
        feather.replace();
        return;
    }

    loansList.innerHTML = filteredLoans.map(loan => renderLoanItem(loan)).join('');
    feather.replace();
}

function renderLoanItem(loan) {
    const iconClass = `loan-icon loan-icon-${loan.loan_type}`;
    const iconName = getLoanIcon(loan.loan_type);
    
    return `
        <div class="loan-item ${loan.is_active ? '' : 'paid-off'}">
            <div class="loan-header">
                <div class="loan-main">
                    <div class="${iconClass}">
                        <i data-feather="${iconName}"></i>
                    </div>
                    <div class="loan-info">
                        <h4>
                            ${escapeHtml(loan.name)}
                            ${!loan.is_active ? '<span class="badge-paid">Paid Off</span>' : ''}
                        </h4>
                        <div class="loan-meta">
                            <span><i data-feather="tag"></i> ${loan.loan_type_display}</span>
                            <span><i data-feather="percent"></i> ${loan.interest_rate}% APR</span>
                            <span><i data-feather="calendar"></i> ${loan.term_months} months</span>
                            ${loan.monthly_payment ? `<span><i data-feather="dollar-sign"></i> ${formatCurrency(loan.monthly_payment)}/mo</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="loan-actions">
                    <button class="btn btn-ghost btn-sm" onclick="viewAmortization(${loan.id})" title="View Amortization">
                        <i data-feather="list"></i>
                    </button>
                    ${loan.is_active ? `
                        <button class="btn btn-ghost btn-sm" onclick="openPaymentModal(${loan.id})" title="Record Payment">
                            <i data-feather="credit-card"></i>
                        </button>
                    ` : ''}
                    <button class="btn btn-ghost btn-sm" onclick="editLoan(${loan.id})" title="Edit">
                        <i data-feather="edit-2"></i>
                    </button>
                    <button class="btn btn-ghost btn-sm" onclick="promptDeleteLoan(${loan.id})" title="Delete">
                        <i data-feather="trash-2"></i>
                    </button>
                </div>
            </div>
            
            <div class="loan-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${loan.progress_percent}%"></div>
                </div>
                <div class="progress-labels">
                    <span>Balance: ${formatCurrency(loan.current_balance)}</span>
                    <span>${loan.progress_percent}% paid</span>
                    <span>Original: ${formatCurrency(loan.original_principal)}</span>
                </div>
            </div>
        </div>
    `;
}

function getLoanIcon(type) {
    const icons = {
        mortgage: 'home',
        auto: 'truck',
        personal: 'user',
        student: 'book',
        other: 'file-text'
    };
    return icons[type] || 'file-text';
}

function updateSummary(data) {
    const activeLoans = loans.filter(l => l.is_active);
    activeCountEl.textContent = activeLoans.length;
    totalBalanceEl.textContent = formatCurrency(data.total_balance);
    
    const monthlyTotal = activeLoans.reduce((sum, l) => sum + (l.monthly_payment || 0), 0);
    monthlyPaymentsEl.textContent = formatCurrency(monthlyTotal);
}

function populateAccountSelect() {
    const select = document.getElementById('loan-account');
    select.innerHTML = '<option value="">No linked account</option>';
    
    accounts.forEach(account => {
        const option = document.createElement('option');
        option.value = account.id;
        option.textContent = account.name;
        select.appendChild(option);
    });
}

function openLoanModal(loan = null) {
    editingLoanId = loan ? loan.id : null;
    modalTitle.textContent = loan ? 'Edit Loan' : 'Add Loan';
    
    if (loan) {
        document.getElementById('loan-name').value = loan.name;
        document.getElementById('loan-type').value = loan.loan_type;
        document.getElementById('loan-principal').value = loan.original_principal;
        document.getElementById('loan-rate').value = loan.interest_rate;
        document.getElementById('loan-term').value = loan.term_months;
        document.getElementById('loan-start-date').value = loan.start_date;
        document.getElementById('loan-payment').value = loan.monthly_payment || '';
        document.getElementById('loan-account').value = loan.account_id || '';
        document.getElementById('loan-notes').value = loan.notes || '';
        
        document.getElementById('loan-principal').disabled = true;
        document.getElementById('loan-term').disabled = true;
        document.getElementById('loan-start-date').disabled = true;
    } else {
        loanForm.reset();
        document.getElementById('loan-start-date').value = new Date().toISOString().split('T')[0];
        document.getElementById('loan-principal').disabled = false;
        document.getElementById('loan-term').disabled = false;
        document.getElementById('loan-start-date').disabled = false;
    }
    
    loanModal.classList.add('active');
}

function closeLoanModal() {
    loanModal.classList.remove('active');
    editingLoanId = null;
    loanForm.reset();
}

async function handleLoanSubmit(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('loan-name').value,
        loan_type: document.getElementById('loan-type').value,
        interest_rate: parseFloat(document.getElementById('loan-rate').value),
        account_id: document.getElementById('loan-account').value || null,
        notes: document.getElementById('loan-notes').value || null
    };
    
    if (!editingLoanId) {
        data.original_principal = parseFloat(document.getElementById('loan-principal').value);
        data.term_months = parseInt(document.getElementById('loan-term').value);
        data.start_date = document.getElementById('loan-start-date').value;
    }
    
    const paymentValue = document.getElementById('loan-payment').value;
    if (paymentValue) {
        data.monthly_payment = parseFloat(paymentValue);
    }
    
    try {
        if (editingLoanId) {
            await updateLoan(editingLoanId, data);
            showNotification('Loan updated successfully', 'success');
        } else {
            await createLoan(data);
            showNotification('Loan created successfully', 'success');
        }
        
        closeLoanModal();
        await loadLoans();
    } catch (error) {
        console.error('Failed to save loan:', error);
        showNotification(error.message || 'Failed to save loan', 'error');
    }
}

function editLoan(id) {
    const loan = loans.find(l => l.id === id);
    if (loan) {
        openLoanModal(loan);
    }
}

function openPaymentModal(loanId) {
    const loan = loans.find(l => l.id === loanId);
    if (!loan) return;
    
    paymentLoanId = loanId;
    
    document.getElementById('payment-loan-name').textContent = loan.name;
    document.getElementById('payment-current-balance').textContent = formatCurrency(loan.current_balance);
    document.getElementById('payment-amount').value = loan.monthly_payment || '';
    document.getElementById('payment-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('payment-extra').value = '';
    document.getElementById('payment-notes').value = '';
    
    paymentModal.classList.add('active');
}

function closePaymentModal() {
    paymentModal.classList.remove('active');
    paymentLoanId = null;
    paymentForm.reset();
}

async function handlePaymentSubmit(e) {
    e.preventDefault();
    
    if (!paymentLoanId) return;
    
    const data = {
        amount: parseFloat(document.getElementById('payment-amount').value),
        payment_date: document.getElementById('payment-date').value,
        extra_principal: parseFloat(document.getElementById('payment-extra').value) || 0,
        notes: document.getElementById('payment-notes').value || null
    };
    
    try {
        const result = await recordPayment(paymentLoanId, data);
        showNotification(`Payment recorded: ${formatCurrency(result.principal_paid)} principal, ${formatCurrency(result.interest_paid)} interest`, 'success');
        closePaymentModal();
        await loadLoans();
    } catch (error) {
        console.error('Failed to record payment:', error);
        showNotification(error.message || 'Failed to record payment', 'error');
    }
}

async function viewAmortization(loanId) {
    try {
        const schedule = await getAmortizationSchedule(loanId);
        
        document.getElementById('amort-title').textContent = `Amortization: ${schedule.loan_name}`;
        document.getElementById('amort-principal').textContent = formatCurrency(schedule.original_principal);
        document.getElementById('amort-rate').textContent = `${schedule.interest_rate}%`;
        document.getElementById('amort-term').textContent = `${schedule.term_months} months`;
        document.getElementById('amort-payment').textContent = formatCurrency(schedule.monthly_payment);
        document.getElementById('amort-total-interest').textContent = formatCurrency(schedule.total_interest);
        document.getElementById('amort-total-cost').textContent = formatCurrency(schedule.total_cost);
        
        const tbody = document.getElementById('amort-schedule');
        tbody.innerHTML = schedule.schedule.map(entry => `
            <tr>
                <td>${entry.payment_number}</td>
                <td>${formatDate(entry.payment_date)}</td>
                <td>${formatCurrency(entry.payment_amount)}</td>
                <td>${formatCurrency(entry.principal)}</td>
                <td>${formatCurrency(entry.interest)}</td>
                <td>${formatCurrency(entry.balance)}</td>
            </tr>
        `).join('');
        
        amortModal.classList.add('active');
    } catch (error) {
        console.error('Failed to load amortization schedule:', error);
        showNotification('Failed to load amortization schedule', 'error');
    }
}

function closeAmortModal() {
    amortModal.classList.remove('active');
}

function promptDeleteLoan(id) {
    deletingLoanId = id;
    deleteModal.classList.add('active');
}

function closeDeleteModal() {
    deleteModal.classList.remove('active');
    deletingLoanId = null;
}

async function confirmDelete() {
    if (!deletingLoanId) return;
    
    try {
        await deleteLoan(deletingLoanId);
        showNotification('Loan deleted', 'success');
        closeDeleteModal();
        await loadLoans();
    } catch (error) {
        console.error('Failed to delete loan:', error);
        showNotification('Failed to delete loan', 'error');
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${escapeHtml(message)}</span>
        <button class="notification-close">&times;</button>
    `;
    
    if (!document.getElementById('notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 12px;
                z-index: 1001;
                animation: slideIn 0.3s ease;
            }
            .notification-success { border-color: var(--accent-green); }
            .notification-error { border-color: var(--accent-red); }
            .notification-close {
                background: none;
                border: none;
                color: var(--text-muted);
                cursor: pointer;
                font-size: 18px;
                padding: 0;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(styles);
    }
    
    document.body.appendChild(notification);
    
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 4000);
}

window.openLoanModal = openLoanModal;
window.editLoan = editLoan;
window.promptDeleteLoan = promptDeleteLoan;
window.openPaymentModal = openPaymentModal;
window.viewAmortization = viewAmortization;
