/**
 * Subscriptions Page JavaScript
 */

let subscriptions = [];
let accounts = [];
let categories = [];
let editingSubscriptionId = null;
let deletingSubscriptionId = null;
let currentFilter = 'all';

const subscriptionsList = document.getElementById('subscriptions-list');
const addSubscriptionBtn = document.getElementById('add-subscription-btn');
const subscriptionModal = document.getElementById('subscription-modal');
const subscriptionForm = document.getElementById('subscription-form');
const modalTitle = document.getElementById('modal-title');
const modalClose = document.getElementById('modal-close');
const modalCancel = document.getElementById('modal-cancel');
const deleteModal = document.getElementById('delete-modal');
const deleteModalClose = document.getElementById('delete-modal-close');
const deleteCancel = document.getElementById('delete-cancel');
const deleteConfirm = document.getElementById('delete-confirm');
const logoutBtn = document.getElementById('logout-btn');
const isActiveGroup = document.getElementById('is-active-group');

const activeCountEl = document.getElementById('active-count');
const monthlyCostEl = document.getElementById('monthly-cost');
const yearlyCostEl = document.getElementById('yearly-cost');

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
        loadSubscriptions(),
        loadAccounts(),
        loadCategories()
    ]);

    setupEventListeners();
}

function setupEventListeners() {
    addSubscriptionBtn.addEventListener('click', () => openSubscriptionModal());

    modalClose.addEventListener('click', closeSubscriptionModal);
    modalCancel.addEventListener('click', closeSubscriptionModal);
    subscriptionModal.addEventListener('click', (e) => {
        if (e.target === subscriptionModal) closeSubscriptionModal();
    });

    subscriptionForm.addEventListener('submit', handleSubscriptionSubmit);

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
            renderSubscriptions();
        });
    });

    logoutBtn.addEventListener('click', () => {
        logout();
        window.location.href = '/login';
    });
}

async function loadSubscriptions() {
    try {
        const data = await apiRequest('/api/subscriptions');
        subscriptions = data.subscriptions;
        updateSummary(data);
        renderSubscriptions();
    } catch (error) {
        console.error('Failed to load subscriptions:', error);
        showNotification('Failed to load subscriptions', 'error');
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

async function loadCategories() {
    try {
        const data = await apiRequest('/api/categories');
        categories = data.categories;
        populateCategorySelect();
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

async function createSubscription(data) {
    return await apiRequest('/api/subscriptions', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function updateSubscription(id, data) {
    return await apiRequest(`/api/subscriptions/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    });
}

async function deleteSubscription(id) {
    return await apiRequest(`/api/subscriptions/${id}`, {
        method: 'DELETE'
    });
}

function renderSubscriptions() {
    let filteredSubscriptions = subscriptions;

    if (currentFilter === 'active') {
        filteredSubscriptions = subscriptions.filter(s => s.is_active);
    } else if (currentFilter === 'inactive') {
        filteredSubscriptions = subscriptions.filter(s => !s.is_active);
    }

    if (filteredSubscriptions.length === 0) {
        subscriptionsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon"><i data-feather="repeat" style="width: 48px; height: 48px;"></i></div>
                <div class="empty-state-title">${currentFilter === 'all' ? 'No subscriptions yet' : `No ${currentFilter} subscriptions`}</div>
                <div class="empty-state-text">${currentFilter === 'all' ? 'Track your recurring payments and subscriptions.' : ''}</div>
                ${currentFilter === 'all' ? '<button class="btn btn-primary" onclick="openSubscriptionModal()">Add Subscription</button>' : ''}
            </div>
        `;
        feather.replace();
        return;
    }

    subscriptionsList.innerHTML = filteredSubscriptions.map(sub => renderSubscriptionItem(sub)).join('');
    feather.replace();
}

function renderSubscriptionItem(sub) {
    const renewalBadge = getRenewalBadge(sub.days_until_renewal);
    
    return `
        <div class="subscription-item ${sub.is_active ? '' : 'inactive'}">
            <div class="subscription-main">
                <div class="subscription-icon ${sub.is_active ? '' : 'inactive'}">
                    <i data-feather="repeat"></i>
                </div>
                <div class="subscription-info">
                    <div class="subscription-name">
                        ${escapeHtml(sub.name)}
                        ${!sub.is_active ? '<span class="badge badge-secondary">Inactive</span>' : ''}
                        ${renewalBadge}
                    </div>
                    <div class="subscription-details">
                        ${sub.account_name ? `<span><i data-feather="credit-card"></i> ${escapeHtml(sub.account_name)}</span>` : ''}
                        ${sub.category_name ? `<span><i data-feather="tag"></i> ${escapeHtml(sub.category_name)}</span>` : ''}
                        <span><i data-feather="calendar"></i> Next: ${formatDate(sub.next_billing_date)}</span>
                    </div>
                </div>
            </div>
            <div class="subscription-amount">
                <div class="subscription-amount-value">${formatCurrency(sub.amount)}</div>
                <div class="subscription-amount-cycle">${sub.billing_cycle_display}</div>
            </div>
            <div class="subscription-actions">
                <button class="btn btn-ghost btn-sm" onclick="editSubscription(${sub.id})" title="Edit">
                    <i data-feather="edit-2"></i>
                </button>
                <button class="btn btn-ghost btn-sm" onclick="promptDeleteSubscription(${sub.id})" title="Delete">
                    <i data-feather="trash-2"></i>
                </button>
            </div>
        </div>
    `;
}

function getRenewalBadge(daysUntil) {
    if (daysUntil < 0) {
        return `<span class="renewal-badge renewal-overdue">Overdue</span>`;
    } else if (daysUntil === 0) {
        return `<span class="renewal-badge renewal-today">Due Today</span>`;
    } else if (daysUntil <= 7) {
        return `<span class="renewal-badge renewal-soon">In ${daysUntil} day${daysUntil === 1 ? '' : 's'}</span>`;
    }
    return '';
}

function updateSummary(data) {
    const activeCount = subscriptions.filter(s => s.is_active).length;
    activeCountEl.textContent = activeCount;
    monthlyCostEl.textContent = formatCurrency(data.total_monthly_cost);
    yearlyCostEl.textContent = formatCurrency(data.total_yearly_cost);
}

function populateAccountSelect() {
    const select = document.getElementById('sub-account');
    select.innerHTML = '<option value="">Select account...</option>';
    
    accounts.forEach(account => {
        const option = document.createElement('option');
        option.value = account.id;
        option.textContent = account.name;
        select.appendChild(option);
    });
}

function populateCategorySelect() {
    const select = document.getElementById('sub-category');
    select.innerHTML = '<option value="">Select category...</option>';
    
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        select.appendChild(option);
    });
}

function openSubscriptionModal(subscription = null) {
    editingSubscriptionId = subscription ? subscription.id : null;
    modalTitle.textContent = subscription ? 'Edit Subscription' : 'Add Subscription';
    
    isActiveGroup.style.display = subscription ? 'block' : 'none';
    
    if (subscription) {
        document.getElementById('sub-name').value = subscription.name;
        document.getElementById('sub-amount').value = subscription.amount;
        document.getElementById('sub-billing-cycle').value = subscription.billing_cycle;
        document.getElementById('sub-next-date').value = subscription.next_billing_date;
        document.getElementById('sub-account').value = subscription.account_id || '';
        document.getElementById('sub-category').value = subscription.category_id || '';
        document.getElementById('sub-notes').value = subscription.notes || '';
        document.getElementById('sub-is-active').checked = subscription.is_active;
    } else {
        subscriptionForm.reset();
        document.getElementById('sub-next-date').value = new Date().toISOString().split('T')[0];
        document.getElementById('sub-is-active').checked = true;
    }
    
    subscriptionModal.classList.add('active');
}

function closeSubscriptionModal() {
    subscriptionModal.classList.remove('active');
    editingSubscriptionId = null;
    subscriptionForm.reset();
}

async function handleSubscriptionSubmit(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('sub-name').value,
        amount: parseFloat(document.getElementById('sub-amount').value),
        billing_cycle: document.getElementById('sub-billing-cycle').value,
        next_billing_date: document.getElementById('sub-next-date').value,
        account_id: document.getElementById('sub-account').value || null,
        category_id: document.getElementById('sub-category').value || null,
        notes: document.getElementById('sub-notes').value || null
    };
    
    if (editingSubscriptionId) {
        data.is_active = document.getElementById('sub-is-active').checked;
    }
    
    try {
        if (editingSubscriptionId) {
            await updateSubscription(editingSubscriptionId, data);
            showNotification('Subscription updated successfully', 'success');
        } else {
            await createSubscription(data);
            showNotification('Subscription created successfully', 'success');
        }
        
        closeSubscriptionModal();
        await loadSubscriptions();
    } catch (error) {
        console.error('Failed to save subscription:', error);
        showNotification(error.message || 'Failed to save subscription', 'error');
    }
}

function editSubscription(id) {
    const subscription = subscriptions.find(s => s.id === id);
    if (subscription) {
        openSubscriptionModal(subscription);
    }
}

function promptDeleteSubscription(id) {
    deletingSubscriptionId = id;
    deleteModal.classList.add('active');
}

function closeDeleteModal() {
    deleteModal.classList.remove('active');
    deletingSubscriptionId = null;
}

async function confirmDelete() {
    if (!deletingSubscriptionId) return;
    
    try {
        await deleteSubscription(deletingSubscriptionId);
        showNotification('Subscription deleted', 'success');
        closeDeleteModal();
        await loadSubscriptions();
    } catch (error) {
        console.error('Failed to delete subscription:', error);
        showNotification('Failed to delete subscription', 'error');
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
    }, 3000);
}

window.openSubscriptionModal = openSubscriptionModal;
window.editSubscription = editSubscription;
window.promptDeleteSubscription = promptDeleteSubscription;
