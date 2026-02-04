// Reports page functionality

let categoryChart = null;
let trendsChart = null;

const chartColors = [
    'rgba(97, 175, 239, 0.8)',
    'rgba(152, 195, 121, 0.8)',
    'rgba(224, 108, 117, 0.8)',
    'rgba(229, 192, 123, 0.8)',
    'rgba(198, 120, 221, 0.8)',
    'rgba(86, 182, 194, 0.8)',
    'rgba(171, 178, 191, 0.8)',
    'rgba(209, 154, 102, 0.8)',
];

document.addEventListener('DOMContentLoaded', function() {
    feather.replace();
    checkAuth();
    initializeDateRange();
    loadReportsData();
    
    document.getElementById('quick-range').addEventListener('change', handleQuickRange);
    document.getElementById('apply-range').addEventListener('click', loadReportsData);
    document.getElementById('logout-btn').addEventListener('click', logout);
});

function initializeDateRange() {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    document.getElementById('start-date').value = formatDate(firstDay);
    document.getElementById('end-date').value = formatDate(lastDay);
}

function handleQuickRange() {
    const range = document.getElementById('quick-range').value;
    const now = new Date();
    let startDate, endDate;
    
    switch(range) {
        case 'this-month':
            startDate = new Date(now.getFullYear(), now.getMonth(), 1);
            endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
            break;
        case 'last-month':
            startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
            endDate = new Date(now.getFullYear(), now.getMonth(), 0);
            break;
        case 'last-3-months':
            startDate = new Date(now.getFullYear(), now.getMonth() - 2, 1);
            endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
            break;
        case 'last-6-months':
            startDate = new Date(now.getFullYear(), now.getMonth() - 5, 1);
            endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
            break;
        case 'this-year':
            startDate = new Date(now.getFullYear(), 0, 1);
            endDate = new Date(now.getFullYear(), 11, 31);
            break;
        case 'last-year':
            startDate = new Date(now.getFullYear() - 1, 0, 1);
            endDate = new Date(now.getFullYear() - 1, 11, 31);
            break;
        case 'custom':
            return;
    }
    
    document.getElementById('start-date').value = formatDate(startDate);
    document.getElementById('end-date').value = formatDate(endDate);
}

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

async function loadReportsData() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    try {
        const [categoryData, trendsData] = await Promise.all([
            api.get(`/api/reports/spending-by-category?start_date=${startDate}&end_date=${endDate}`),
            api.get(`/api/reports/spending-trends?months=6`)
        ]);
        
        updateSummaryStats(categoryData);
        renderCategoryChart(categoryData);
        renderCategoryTable(categoryData);
        renderTrendsChart(trendsData);
    } catch (error) {
        console.error('Error loading reports:', error);
        showToast('Failed to load reports', 'error');
    }
}

function updateSummaryStats(data) {
    document.getElementById('total-income').textContent = formatCurrency(data.total_income);
    document.getElementById('total-spending').textContent = formatCurrency(data.total_spending);
    
    const net = data.total_income - data.total_spending;
    const netElement = document.getElementById('net-amount');
    netElement.textContent = formatCurrency(Math.abs(net));
    if (net >= 0) {
        netElement.textContent = '+' + netElement.textContent;
        netElement.style.color = 'var(--accent-green)';
    } else {
        netElement.textContent = '-' + netElement.textContent;
        netElement.style.color = 'var(--accent-red)';
    }
}

function renderCategoryChart(data) {
    const ctx = document.getElementById('category-chart').getContext('2d');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    if (data.categories.length === 0) {
        document.getElementById('category-legend').innerHTML = '<p style="color: var(--text-muted);">No spending data for this period</p>';
        return;
    }
    
    const categories = data.categories;
    const labels = categories.map(c => c.category_name);
    const values = categories.map(c => c.total);
    const colors = categories.map((_, i) => chartColors[i % chartColors.length]);
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: 'var(--bg-secondary)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = formatCurrency(context.raw);
                            const percentage = categories[context.dataIndex].percentage.toFixed(1);
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    const legendHtml = categories.map((c, i) => `
        <div class="legend-item">
            <div class="legend-color" style="background: ${colors[i]}"></div>
            <span>${c.category_name}</span>
        </div>
    `).join('');
    document.getElementById('category-legend').innerHTML = legendHtml;
}

function renderCategoryTable(data) {
    const tbody = document.getElementById('category-tbody');
    
    if (data.categories.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No spending data</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.categories.map((cat, i) => `
        <tr>
            <td>
                <div style="display: flex; align-items: center; gap: var(--spacing-sm);">
                    <div class="legend-color" style="background: ${chartColors[i % chartColors.length]}"></div>
                    ${cat.category_name}
                </div>
            </td>
            <td class="text-right">${cat.transaction_count}</td>
            <td class="text-right">${formatCurrency(cat.total)}</td>
            <td class="text-right">
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: var(--spacing-sm);">
                    <div class="progress-bar-small">
                        <div class="progress-fill" style="width: ${cat.percentage}%; background: ${chartColors[i % chartColors.length]};"></div>
                    </div>
                    <span>${cat.percentage.toFixed(1)}%</span>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderTrendsChart(data) {
    const ctx = document.getElementById('trends-chart').getContext('2d');
    
    if (trendsChart) {
        trendsChart.destroy();
    }
    
    if (data.months.length === 0) {
        return;
    }
    
    const months = data.months;
    const labels = months.map(m => m.month_label);
    const incomeData = months.map(m => m.income);
    const expenseData = months.map(m => m.expenses);
    const netData = months.map(m => m.net);
    
    trendsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    backgroundColor: 'rgba(152, 195, 121, 0.8)',
                    borderColor: 'rgba(152, 195, 121, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    backgroundColor: 'rgba(224, 108, 117, 0.8)',
                    borderColor: 'rgba(224, 108, 117, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        color: 'rgba(171, 178, 191, 0.1)'
                    },
                    ticks: {
                        color: 'var(--text-muted)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(171, 178, 191, 0.1)'
                    },
                    ticks: {
                        color: 'var(--text-muted)',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: 'var(--text-primary)',
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            }
        }
    });
}

async function exportTransactions() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    try {
        const response = await fetch(`/api/reports/export/transactions?start_date=${startDate}&end_date=${endDate}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        downloadBlob(blob, `transactions_${startDate}_to_${endDate}.csv`);
        showToast('Transactions exported successfully', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showToast('Failed to export transactions', 'error');
    }
}

async function exportAccounts() {
    try {
        const response = await fetch('/api/reports/export/accounts', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        downloadBlob(blob, `accounts_${formatDate(new Date())}.csv`);
        showToast('Accounts exported successfully', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showToast('Failed to export accounts', 'error');
    }
}

async function exportSubscriptions() {
    try {
        const response = await fetch('/api/reports/export/subscriptions', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        downloadBlob(blob, `subscriptions_${formatDate(new Date())}.csv`);
        showToast('Subscriptions exported successfully', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showToast('Failed to export subscriptions', 'error');
    }
}

async function exportLoans() {
    try {
        const response = await fetch('/api/reports/export/loans', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        downloadBlob(blob, `loans_${formatDate(new Date())}.csv`);
        showToast('Loans exported successfully', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showToast('Failed to export loans', 'error');
    }
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}
