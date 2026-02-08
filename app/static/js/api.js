/**
 * API Helper Module
 * 
 * Provides convenient methods for making API requests.
 * All requests are relative to /api/ and include credentials (cookies).
 */

const api = {
    baseUrl: '/api',
    
    /**
     * Make a GET request
     */
    async get(endpoint) {
        return fetch(`${this.baseUrl}${endpoint}`, {
            method: 'GET',
            credentials: 'same-origin',
        });
    },
    
    /**
     * Make a POST request with JSON body
     */
    async post(endpoint, data = null) {
        const options = {
            method: 'POST',
            credentials: 'same-origin',
            headers: {},
        };
        
        if (data) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }
        
        return fetch(`${this.baseUrl}${endpoint}`, options);
    },
    
    /**
     * Make a PATCH request with JSON body
     */
    async patch(endpoint, data) {
        return fetch(`${this.baseUrl}${endpoint}`, {
            method: 'PATCH',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
    },
    
    /**
     * Make a DELETE request
     */
    async delete(endpoint) {
        return fetch(`${this.baseUrl}${endpoint}`, {
            method: 'DELETE',
            credentials: 'same-origin',
        });
    },
};

/**
 * Format a number as currency (USD)
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(amount);
}

/**
 * Format a date string
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

/**
 * Parse currency input (remove $ and commas)
 */
function parseCurrency(value) {
    if (typeof value === 'number') return value;
    return parseFloat(value.replace(/[$,]/g, '')) || 0;
}

/**
 * Show a toast notification (simple implementation)
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
        min-width: 250px;
        box-shadow: var(--shadow-lg);
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

/**
 * Check if the user has an active session.
 * Auth is handled via HTTP-only cookies, so we can't inspect the token directly.
 * Returns true to let init proceed; API calls will handle 401 redirects.
 */
function getToken() {
    return true;
}

/**
 * Make an authenticated API request and return parsed JSON.
 * Redirects to /login on 401 responses.
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        credentials: 'same-origin',
        headers: {},
    };

    if (options.body) {
        defaultOptions.headers['Content-Type'] = 'application/json';
    }

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    const response = await fetch(url, mergedOptions);

    if (response.status === 401) {
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || 'Request failed');
    }

    const text = await response.text();
    return text ? JSON.parse(text) : {};
}

/**
 * Verify the session is valid by making a lightweight API call.
 */
function checkAuth() {
    api.get('/accounts/summary').then(response => {
        if (!response.ok) {
            window.location.href = '/login';
        }
    }).catch(() => {
        window.location.href = '/login';
    });
}

/**
 * Log out by clearing the server session and redirecting to login.
 */
function logout() {
    api.post('/auth/logout').catch(() => {});
    window.location.href = '/login';
}
