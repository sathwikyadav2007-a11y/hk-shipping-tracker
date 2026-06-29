// HK Shipping Private Limited - Frontend JS Logic & Wizard Management

// Authentication & Page Access Guards
(function() {
    const isPublicPage = window.location.pathname === '/' || window.location.pathname === '/login';
    if (!isPublicPage && !localStorage.getItem('hks_auth_token')) {
        window.location.href = '/login';
    }
})();

// Global Logout Function
window.logoutUser = function() {
    localStorage.removeItem('hks_auth_token');
    localStorage.removeItem('hks_user_role');
    localStorage.removeItem('hks_user_username');
    localStorage.removeItem('hks_user_email');
    window.location.href = '/login';
}

// Global Role Switcher Function
window.switchUserRole = function(role, username) {
    localStorage.setItem('hks_user_role', role);
    localStorage.setItem('hks_user_username', username);
    window.location.reload();
}

// Global Fetch Interceptor to append RBAC Headers
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    if (!options.headers) {
        options.headers = {};
    }
    const role = localStorage.getItem('hks_user_role') || 'Customer';
    const username = localStorage.getItem('hks_user_username') || 'customer_user';
    
    if (options.headers instanceof Headers) {
        options.headers.set('X-User-Role', role);
        options.headers.set('X-User-Username', username);
    } else if (Array.isArray(options.headers)) {
        options.headers.push(['X-User-Role', role]);
        options.headers.push(['X-User-Username', username]);
    } else if (typeof options.headers === 'object') {
        options.headers['X-User-Role'] = role;
        options.headers['X-User-Username'] = username;
    }
    
    return originalFetch(url, options);
};

// Booking Channel Gatekeeper / Password Protection Layer
(function() {
    const isBookingStartPage = window.location.pathname === '/booking/crm';
    
    if (isBookingStartPage) {
        const isAuth = sessionStorage.getItem('hks_booking_authenticated') === 'true';
        if (!isAuth) {
            // Apply lock class to body immediately on load
            document.addEventListener('DOMContentLoaded', () => {
                document.body.classList.add('booking-locked');
                showPasswordPrompt();
            });
        }
    }
})();

// Intercept clicks on New Booking links across all pages
document.addEventListener('DOMContentLoaded', () => {
    document.body.addEventListener('click', (e) => {
        const targetLink = e.target.closest('a[href*="/booking/crm"]');
        if (targetLink) {
            const isAuth = sessionStorage.getItem('hks_booking_authenticated') === 'true';
            if (!isAuth) {
                e.preventDefault();
                showPasswordPrompt(() => {
                    window.location.href = targetLink.getAttribute('href');
                });
            }
        }
    });
});

function showPasswordPrompt(successCallback) {
    if (document.querySelector('.auth-overlay-container')) return;

    const overlay = document.createElement('div');
    overlay.className = 'auth-overlay-container d-flex align-items-center justify-content-center';
    overlay.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:100vh; background: linear-gradient(135deg, #0b0f19 0%, #111827 100%); z-index:99999; color: white;';
    
    overlay.innerHTML = `
        <div class="card p-5 border-0 shadow-lg text-center" style="width: 420px; background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;">
            <div class="mb-4">
                <div class="d-inline-flex align-items-center justify-content-center bg-danger bg-opacity-10 text-danger rounded-circle mb-3" style="width: 75px; height: 75px;">
                    <i class="bi bi-shield-lock-fill fs-1"></i>
                </div>
                <h3 class="fw-bold text-white mb-2">Gatekeeper Security</h3>
                <p class="text-white-50 small mb-0">Authorized personnel only. Please verify the passcode to unlock the freight booking system.</p>
            </div>
            <form id="bookingAuthForm" novalidate>
                <div class="mb-4">
                    <label for="bookingPassword" class="form-label text-start d-block fw-semibold text-white-50 small mb-2">System Passcode</label>
                    <input type="password" class="form-control bg-dark border-secondary text-white text-center fs-5 py-2" id="bookingPassword" placeholder="••••••••" required>
                    <div class="text-danger mt-2 small fw-semibold" id="authErrorMsg" style="display: none;"></div>
                </div>
                <button type="submit" class="btn btn-info w-100 py-3 fw-bold text-white shadow-sm">
                    <i class="bi bi-unlock-fill me-2"></i>Verify & Grant Access
                </button>
            </form>
        </div>
    `;

    document.body.appendChild(overlay);

    const form = document.getElementById('bookingAuthForm');
    const passwordInput = document.getElementById('bookingPassword');
    const errorMsg = document.getElementById('authErrorMsg');

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const passcode = 'hkshipping2026';
        
        if (passwordInput.value === passcode) {
            sessionStorage.setItem('hks_booking_authenticated', 'true');
            overlay.remove();
            if (typeof successCallback === 'function') {
                successCallback();
            } else {
                document.body.classList.remove('booking-locked');
            }
        } else {
            errorMsg.innerText = 'Incorrect security passcode. Access Denied.';
            errorMsg.style.display = 'block';
            passwordInput.classList.add('is-invalid');
            passwordInput.focus();
            
            const card = overlay.querySelector('.card');
            card.style.animation = 'shake 0.3s ease-in-out';
            setTimeout(() => {
                card.style.animation = '';
            }, 300);
        }
    });

    passwordInput.addEventListener('input', () => {
        passwordInput.classList.remove('is-invalid');
        errorMsg.style.display = 'none';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize active role in storage
    const activeRole = localStorage.getItem('hks_user_role') || 'Customer';
    const activeUsername = localStorage.getItem('hks_user_username') || 'customer_user';
    localStorage.setItem('hks_user_role', activeRole);
    localStorage.setItem('hks_user_username', activeUsername);

    // Inject Logout option dynamically into the role switcher dropdown
    const dropdownMenus = document.querySelectorAll('.dropdown-menu');
    dropdownMenus.forEach(menu => {
        if (menu.innerHTML.includes('switchUserRole') && !menu.innerHTML.includes('logoutUser')) {
            const divider = document.createElement('li');
            divider.innerHTML = '<hr class="dropdown-divider">';
            const logoutItem = document.createElement('li');
            logoutItem.innerHTML = '<a class="dropdown-item fw-bold text-danger" href="#" onclick="logoutUser()"><i class="bi bi-box-arrow-right me-2"></i>Logout</a>';
            menu.appendChild(divider);
            menu.appendChild(logoutItem);
        }
    });

    const displaySpan = document.getElementById('currentRoleDisplay');
    if (displaySpan) {
        displaySpan.innerText = activeRole;
    }

    // Identify which form or panel is active
    const crmForm = document.getElementById('crmForm');
    const tripForm = document.getElementById('tripForm');
    const fleetForm = document.getElementById('fleetForm');
    const accountsForm = document.getElementById('accountsForm');
    const dashboardStats = document.getElementById('dashboardStats');

    if (crmForm) {
        setupCRMStep();
    } else if (tripForm) {
        setupTripStep();
    } else if (fleetForm) {
        setupFleetStep();
    } else if (accountsForm) {
        setupAccountsStep();
    } else if (dashboardStats) {
        setupDashboardPage();
    }
});

/**
 * Helper: Save multiple key-value pairs to sessionStorage
 */
function saveStepData(dataObj) {
    Object.keys(dataObj).forEach(key => {
        if (dataObj[key] !== undefined && dataObj[key] !== null) {
            sessionStorage.setItem('hks_' + key, dataObj[key]);
        }
    });
}

/**
 * Helper: Retrieve item from sessionStorage
 */
function getStepData(key) {
    return sessionStorage.getItem('hks_' + key) || '';
}

/**
 * Step 1: Customer Logistics CRM Page
 */
function setupCRMStep() {
    const form = document.getElementById('crmForm');
    
    // Pre-populate if back-navigated
    document.getElementById('customer_name').value = getStepData('customer_name');
    document.getElementById('customer_email').value = getStepData('customer_email');
    document.getElementById('customer_phone').value = getStepData('customer_phone');

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        if (!form.checkValidity()) {
            e.stopPropagation();
            form.classList.add('was-validated');
            return;
        }

        // Save fields
        saveStepData({
            customer_name: document.getElementById('customer_name').value,
            customer_email: document.getElementById('customer_email').value,
            customer_phone: document.getElementById('customer_phone').value
        });

        // Redirect to Step 2
        window.location.href = '/booking/trip';
    });
}

/**
 * Step 2: Trip & Cargo Details Page
 */
function setupTripStep() {
    const form = document.getElementById('tripForm');
    const backBtn = document.getElementById('backBtn');

    // Pre-populate
    document.getElementById('pickup_location').value = getStepData('pickup_location');
    document.getElementById('drop_location').value = getStepData('drop_location');
    document.getElementById('goods_type').value = getStepData('goods_type');
    document.getElementById('weight').value = getStepData('weight');
    document.getElementById('preferred_date').value = getStepData('preferred_date');
    document.getElementById('gps_checkpoint').value = getStepData('gps_checkpoint');
    document.getElementById('eta').value = getStepData('eta');

    // Navigation
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            // Save state in case they made changes before hitting back
            saveStepData({
                pickup_location: document.getElementById('pickup_location').value,
                drop_location: document.getElementById('drop_location').value,
                goods_type: document.getElementById('goods_type').value,
                weight: document.getElementById('weight').value,
                preferred_date: document.getElementById('preferred_date').value,
                gps_checkpoint: document.getElementById('gps_checkpoint').value,
                eta: document.getElementById('eta').value
            });
            window.location.href = '/booking/crm';
        });
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        if (!form.checkValidity()) {
            e.stopPropagation();
            form.classList.add('was-validated');
            return;
        }

        saveStepData({
            pickup_location: document.getElementById('pickup_location').value,
            drop_location: document.getElementById('drop_location').value,
            goods_type: document.getElementById('goods_type').value,
            weight: document.getElementById('weight').value,
            preferred_date: document.getElementById('preferred_date').value,
            gps_checkpoint: document.getElementById('gps_checkpoint').value,
            eta: document.getElementById('eta').value
        });

        window.location.href = '/booking/fleet';
    });
}

/**
 * Step 3: Fleet & Driver Assignment Page
 */
function setupFleetStep() {
    const form = document.getElementById('fleetForm');
    const backBtn = document.getElementById('backBtn');

    // Pre-populate
    document.getElementById('vehicle_number').value = getStepData('vehicle_number');
    document.getElementById('vehicle_type').value = getStepData('vehicle_type');
    document.getElementById('capacity_tons').value = getStepData('capacity_tons');
    document.getElementById('insurance_expiry').value = getStepData('insurance_expiry');
    document.getElementById('permit_expiry').value = getStepData('permit_expiry');
    document.getElementById('maintenance_status').value = getStepData('maintenance_status') || 'Fit';
    document.getElementById('driver_name').value = getStepData('driver_name');
    document.getElementById('driver_phone').value = getStepData('driver_phone');
    document.getElementById('license_number').value = getStepData('license_number');
    document.getElementById('license_expiry').value = getStepData('license_expiry');
    document.getElementById('pod_photo_url').value = getStepData('pod_photo_url');
    document.getElementById('receiver_signature').value = getStepData('receiver_signature');

    // Navigation
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            saveStepData({
                vehicle_number: document.getElementById('vehicle_number').value,
                vehicle_type: document.getElementById('vehicle_type').value,
                capacity_tons: document.getElementById('capacity_tons').value,
                insurance_expiry: document.getElementById('insurance_expiry').value,
                permit_expiry: document.getElementById('permit_expiry').value,
                maintenance_status: document.getElementById('maintenance_status').value,
                driver_name: document.getElementById('driver_name').value,
                driver_phone: document.getElementById('driver_phone').value,
                license_number: document.getElementById('license_number').value,
                license_expiry: document.getElementById('license_expiry').value,
                pod_photo_url: document.getElementById('pod_photo_url').value,
                receiver_signature: document.getElementById('receiver_signature').value
            });
            window.location.href = '/booking/trip';
        });
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        if (!form.checkValidity()) {
            e.stopPropagation();
            form.classList.add('was-validated');
            return;
        }

        saveStepData({
            vehicle_number: document.getElementById('vehicle_number').value,
            vehicle_type: document.getElementById('vehicle_type').value,
            capacity_tons: document.getElementById('capacity_tons').value,
            insurance_expiry: document.getElementById('insurance_expiry').value,
            permit_expiry: document.getElementById('permit_expiry').value,
            maintenance_status: document.getElementById('maintenance_status').value,
            driver_name: document.getElementById('driver_name').value,
            driver_phone: document.getElementById('driver_phone').value,
            license_number: document.getElementById('license_number').value,
            license_expiry: document.getElementById('license_expiry').value,
            pod_photo_url: document.getElementById('pod_photo_url').value,
            receiver_signature: document.getElementById('receiver_signature').value
        });

        window.location.href = '/booking/accounts';
    });
}

/**
 * Step 4: Accounts, Invoicing & Submission Page
 */
function setupAccountsStep() {
    try {
        const form = document.getElementById('accountsForm');
        const backBtn = document.getElementById('backBtn');
        
        const freightInput = document.getElementById('freight_charges');
        const gstRateSelect = document.getElementById('gst_rate');
        const gstAmountInput = document.getElementById('gst_amount');
        const advanceInput = document.getElementById('advance_payment');
        const balanceInput = document.getElementById('balance_payment');
        const statusSelect = document.getElementById('payment_status');
        const dueDateInput = document.getElementById('due_date');

        // Pre-populate
        freightInput.value = getStepData('freight_charges');
        gstRateSelect.value = getStepData('gst_rate') || '5';
        advanceInput.value = getStepData('advance_payment');
        statusSelect.value = getStepData('payment_status') || 'Pending';
        dueDateInput.value = getStepData('due_date');

        // Lock down billing parameters for Customer
        const activeRole = localStorage.getItem('hks_user_role') || 'Customer';
        if (activeRole === 'Customer') {
            freightInput.disabled = true;
            freightInput.removeAttribute('required');
            freightInput.removeAttribute('min');
            gstRateSelect.disabled = true;
            advanceInput.disabled = true;
            statusSelect.disabled = true;
            dueDateInput.disabled = true;
            
            freightInput.value = '0.00';
            gstRateSelect.value = '5';
            gstAmountInput.value = '0.00';
            advanceInput.value = '0.00';
            balanceInput.value = '0.00';
            statusSelect.value = 'Pending';
            dueDateInput.value = '';

            const headerEl = document.querySelector('.card-header-navy');
            if (headerEl) {
                headerEl.innerHTML = '<i class="bi bi-file-earmark-text me-2"></i>Step 4: Review & Submit Booking Request';
            }
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="bi bi-send-fill me-1"></i> Submit Booking Request';
            }
        }

        // Calculation function
        function calculatePayments() {
            const freight = parseFloat(freightInput.value) || 0;
            const gstRate = parseFloat(gstRateSelect.value) || 0;
            
            const gstAmount = parseFloat((freight * (gstRate / 100)).toFixed(2));
            gstAmountInput.value = gstAmount;

            const advance = parseFloat(advanceInput.value) || 0;
            const balance = parseFloat((freight + gstAmount - advance).toFixed(2));
            
            balanceInput.value = balance;
        }

        // Attach listeners
        freightInput.addEventListener('input', calculatePayments);
        gstRateSelect.addEventListener('change', calculatePayments);
        advanceInput.addEventListener('input', calculatePayments);

        // Initial calculation in case fields are pre-populated
        calculatePayments();

        // Navigation Back
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                saveStepData({
                    freight_charges: freightInput.value,
                    gst_rate: gstRateSelect.value,
                    advance_payment: advanceInput.value,
                    payment_status: statusSelect.value,
                    due_date: dueDateInput.value
                });
                window.location.href = '/booking/fleet';
            });
        }

        // Final Wizard Submission Handler
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (!form.checkValidity()) {
                e.stopPropagation();
                form.classList.add('was-validated');
                return;
            }

            // Disable submit button during fetch
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';

            // Gather all stored wizard parameters
            const fullPayload = {
                customer_name: getStepData('customer_name'),
                customer_email: getStepData('customer_email'),
                customer_phone: getStepData('customer_phone'),
                
                pickup_location: getStepData('pickup_location'),
                drop_location: getStepData('drop_location'),
                goods_type: getStepData('goods_type'),
                weight: parseFloat(getStepData('weight')) || 0.0,
                preferred_date: getStepData('preferred_date'),
                gps_checkpoint: getStepData('gps_checkpoint'),
                eta: getStepData('eta'),

                vehicle_number: getStepData('vehicle_number'),
                vehicle_type: getStepData('vehicle_type'),
                capacity_tons: parseFloat(getStepData('capacity_tons')) || 0.0,
                insurance_expiry: getStepData('insurance_expiry'),
                permit_expiry: getStepData('permit_expiry'),
                maintenance_status: getStepData('maintenance_status') || 'Fit',

                driver_name: getStepData('driver_name'),
                driver_phone: getStepData('driver_phone'),
                license_number: getStepData('license_number'),
                license_expiry: getStepData('license_expiry'),

                pod_photo_url: getStepData('pod_photo_url'),
                receiver_signature: getStepData('receiver_signature'),

                freight_charges: parseFloat(freightInput.value) || 0.0,
                gst_rate: parseFloat(gstRateSelect.value) || 0.0,
                gst_amount: parseFloat(gstAmountInput.value) || 0.0,
                advance_payment: parseFloat(advanceInput.value) || 0.0,
                balance_payment: parseFloat(balanceInput.value) || 0.0,
                payment_status: statusSelect.value,
                due_date: dueDateInput.value
            };

            // Check if any critical parameters from earlier steps were lost
            const missingFields = [];
            if (!fullPayload.customer_name) missingFields.push('Customer Name (Step 1)');
            if (!fullPayload.pickup_location) missingFields.push('Pickup Location (Step 2)');
            if (!fullPayload.vehicle_number) missingFields.push('Vehicle Number (Step 3)');
            if (!fullPayload.driver_name) missingFields.push('Driver Name (Step 3)');

            if (missingFields.length > 0) {
                showNotification('danger', 'Form data from previous steps is missing. Please navigate back and check inputs: ' + missingFields.join(', '));
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                return;
            }

            try {
                const response = await fetch('/api/invoices', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(fullPayload)
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || result.details || 'Failed to complete shipment booking.');
                }

                // Clear sessionStorage on success
                clearWizardSession();

                // Redirect to dashboard with success query param or notification
                alert('Booking created successfully! Invoice ID: #INV-' + result.invoice_id);
                window.location.href = '/dashboard';

            } catch (err) {
                console.error('Final Submission Error:', err);
                showNotification('danger', err.message);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    } catch (err) {
        console.error("setupAccountsStep error:", err);
        alert("setupAccountsStep script error: " + err.message + "\nStack: " + err.stack);
    }
}

/**
 * Clear Wizard State from Storage
 */
function clearWizardSession() {
    const keys = [
        'customer_name', 'customer_email', 'customer_phone',
        'pickup_location', 'drop_location', 'goods_type', 'weight', 'preferred_date', 'gps_checkpoint', 'eta',
        'vehicle_number', 'vehicle_type', 'capacity_tons', 'insurance_expiry', 'permit_expiry', 'maintenance_status',
        'driver_name', 'driver_phone', 'license_number', 'license_expiry', 'pod_photo_url', 'receiver_signature',
        'freight_charges', 'gst_rate', 'advance_payment', 'payment_status', 'due_date'
    ];
    keys.forEach(k => sessionStorage.removeItem('hks_' + k));
}


/**
 * Dashboard Setup
 */
function setupDashboardPage() {
    const refreshBtn = document.getElementById('refreshBtn');
    const filterStatus = document.getElementById('filterStatus');
    const filterDate = document.getElementById('filterDate');
    const exportCsvBtn = document.getElementById('exportCsvBtn');

    // Run Frontend Customer lockout adjustments
    const activeRole = localStorage.getItem('hks_user_role') || 'Customer';
    if (activeRole === 'Customer') {
        const statsRow = document.getElementById('statsRow');
        if (statsRow) statsRow.classList.add('d-none');
        
        const sidebar = document.getElementById('sidebarColumn');
        if (sidebar) sidebar.classList.add('d-none');
        
        const mainHistoryCol = document.querySelector('.col-lg-8');
        if (mainHistoryCol) {
            mainHistoryCol.classList.remove('col-lg-8');
            mainHistoryCol.classList.add('col-12');
        }
    } else if (activeRole === 'Admin/Owner') {
        // Load audit logs panel
        loadAuditLogs();
    }

    loadDashboardData();

    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadDashboardData);
    }
    if (filterStatus) {
        filterStatus.addEventListener('change', () => {
            loadInvoices(filterStatus.value, filterDate ? filterDate.value : '');
        });
    }
    if (filterDate) {
        filterDate.addEventListener('change', () => {
            loadInvoices(filterStatus ? filterStatus.value : '', filterDate.value);
        });
    }
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', exportInvoicesToCSV);
    }
}

async function loadDashboardData() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
    }
    showTableLoading();
    try {
        const status = document.getElementById('filterStatus')?.value || '';
        const date = document.getElementById('filterDate')?.value || '';
        const activeRole = localStorage.getItem('hks_user_role') || 'Customer';
        
        if (activeRole === 'Customer') {
            await loadInvoices(status, date);
        } else {
            await Promise.all([loadStats(), loadInvoices(status, date)]);
            if (activeRole === 'Admin/Owner') {
                await loadAuditLogs();
            }
        }
    } catch (e) {
        console.error(e);
        showNotification('danger', 'Error loading dashboard metrics.');
    } finally {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh Data';
        }
    }
}

async function loadStats() {
    const response = await fetch('/api/dashboard/stats');
    const stats = await response.json();
    if (!response.ok) throw new Error(stats.error || 'Failed to fetch stats');

    document.getElementById('totalRevenue').innerText = '₹' + formatCurrency(stats.total_revenue || 0);
    document.getElementById('pendingBalances').innerText = '₹' + formatCurrency(stats.pending_balances || 0);
    document.getElementById('activeTrips').innerText = stats.active_trips || 0;
    document.getElementById('alertCount').innerText = stats.upcoming_compliance_alerts?.length || 0;

    renderComplianceAlerts(stats.upcoming_compliance_alerts || []);
}

async function loadInvoices(status = '', date = '') {
    const tableBody = document.getElementById('invoiceTableBody');
    if (!tableBody) return;

    let url = '/api/invoices';
    const params = [];
    if (status) params.push(`status=${encodeURIComponent(status)}`);
    if (date) params.push(`date=${encodeURIComponent(date)}`);
    if (params.length > 0) url += '?' + params.join('&');

    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to fetch invoices');

    renderInvoiceTable(data);
}

function renderInvoiceTable(invoices) {
    const tableBody = document.getElementById('invoiceTableBody');
    if (!tableBody) return;

    if (!invoices || invoices.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="10" class="py-5 text-center">
                    <div class="empty-state">
                        <i class="bi bi-file-earmark-bar-graph empty-state-icon"></i>
                        <h4 class="empty-state-title">No Records Found</h4>
                        <p class="empty-state-text">There are no consignment invoices matching the current filter options.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    const today = new Date();
    today.setHours(0,0,0,0);

    tableBody.innerHTML = invoices.map(inv => {
        let badgeClass = 'badge-pending';
        if (inv.payment_status?.toLowerCase() === 'paid') {
            badgeClass = 'badge-paid';
        } else if (inv.payment_status?.toLowerCase() === 'pending') {
            badgeClass = 'badge-pending';
        } else if (inv.payment_status?.toLowerCase() === 'partial') {
            badgeClass = 'badge-transit';
        }

        // Calculate due date badges
        let dueDateHtml = '';
        if (inv.payment_status?.toLowerCase() === 'paid') {
            dueDateHtml = `<span class="badge bg-success text-white">Cleared</span>`;
        } else if (inv.due_date) {
            const dueDate = new Date(inv.due_date);
            dueDate.setHours(0,0,0,0);
            const diffTime = dueDate - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays < 0) {
                dueDateHtml = `<span class="badge bg-danger text-white" title="Due: ${inv.due_date}">Overdue (${Math.abs(diffDays)}d)</span>`;
            } else if (diffDays === 0) {
                dueDateHtml = `<span class="badge bg-warning text-dark">Due Today</span>`;
            } else {
                dueDateHtml = `<span class="badge bg-secondary text-white" title="Due Date">${diffDays}d left</span>`;
            }
        } else {
            dueDateHtml = `<span class="text-muted small">N/A</span>`;
        }

        return `
            <tr onclick="window.location.href='/invoices/${inv.id}'" title="Click to view full consignment history & AI details" style="cursor: pointer;">
                <td class="fw-bold">#INV-${inv.id}</td>
                <td>
                    <div class="fw-semibold">${escapeHTML(inv.customer_name || 'N/A')}</div>
                    <small class="text-muted">${escapeHTML(inv.customer_email || '')}</small>
                </td>
                <td>
                    <div><span class="badge bg-secondary">From</span> ${escapeHTML(inv.pickup_location || '')}</div>
                    <div class="mt-1"><span class="badge bg-dark">To</span> ${escapeHTML(inv.drop_location || '')}</div>
                </td>
                <td>
                    <div class="small">No: <strong>${escapeHTML(inv.vehicle_number || '')}</strong></div>
                    <div class="small text-muted">Driver: ${escapeHTML(inv.driver_name || 'Unassigned')}</div>
                </td>
                <td>₹${formatCurrency(inv.freight_charges)}</td>
                <td>₹${formatCurrency(inv.gst_amount)}</td>
                <td>₹${formatCurrency(inv.advance_payment)}</td>
                <td class="fw-semibold text-primary">₹${formatCurrency(inv.balance_payment)}</td>
                <td><span class="badge ${badgeClass}">${escapeHTML(inv.payment_status || 'Pending')}</span></td>
                <td>${dueDateHtml}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Generate and download filtered invoices as a CSV file
 */
async function exportInvoicesToCSV() {
    try {
        const status = document.getElementById('filterStatus')?.value || '';
        const date = document.getElementById('filterDate')?.value || '';
        let url = '/api/invoices';
        const params = [];
        if (status) params.push(`status=${encodeURIComponent(status)}`);
        if (date) params.push(`date=${encodeURIComponent(date)}`);
        if (params.length > 0) url += '?' + params.join('&');

        const response = await fetch(url);
        const invoices = await response.json();
        if (!response.ok) throw new Error(invoices.error || 'Failed to fetch invoices for export');

        if (invoices.length === 0) {
            alert('No records available to export.');
            return;
        }

        // Build CSV string
        const headers = [
            'Invoice ID', 'Customer Name', 'Customer Email', 'Pickup Location', 'Drop Location', 
            'Goods Type', 'Cargo Weight (Tons)', 'Vehicle Number', 'Vehicle Type', 'Driver Name', 
            'Freight Charges (INR)', 'GST Amount (INR)', 'Advance Payment (INR)', 'Balance Payment (INR)', 
            'Payment Status', 'Due Date', 'Created At'
        ];

        const rows = invoices.map(inv => [
            `INV-${inv.id}`,
            inv.customer_name,
            inv.customer_email,
            inv.pickup_location,
            inv.drop_location,
            inv.goods_type,
            inv.weight,
            inv.vehicle_number,
            inv.vehicle_type,
            inv.driver_name,
            inv.freight_charges,
            inv.gst_amount,
            inv.advance_payment,
            inv.balance_payment,
            inv.payment_status,
            inv.due_date || 'N/A',
            inv.created_at
        ]);

        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += [headers.join(','), ...rows.map(e => e.map(val => `"${String(val).replace(/"/g, '""')}"`).join(','))].join('\n');

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `HK_Shipping_Invoices_Export_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (err) {
        console.error(err);
        alert('Failed to export CSV: ' + err.message);
    }
}

function renderComplianceAlerts(alerts) {
    const container = document.getElementById('complianceAlertsContainer');
    if (!container) return;

    if (!alerts || alerts.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="bi bi-shield-check text-success fs-2 d-block mb-2"></i>
                All fleet vehicles & drivers are compliant.
            </div>
        `;
        return;
    }

    container.innerHTML = alerts.map(alert => {
        const isExpired = alert.days_remaining <= 0;
        const itemClass = isExpired ? 'compliance-item' : 'compliance-item warning';
        const badgeColor = isExpired ? 'bg-danger' : 'bg-warning text-dark';
        const labelText = isExpired ? 'Expired' : `${alert.days_remaining} Days Left`;

        return `
            <div class="${itemClass}">
                <div class="d-flex justify-content-between align-items-start">
                    <span class="compliance-title">${escapeHTML(alert.entity_name)}</span>
                    <span class="badge ${badgeColor} btn-sm">${labelText}</span>
                </div>
                <div class="compliance-sub mt-1">
                    <strong>Type:</strong> ${escapeHTML(alert.type)} | <strong>Expiry:</strong> ${alert.expiry_date}
                </div>
                ${alert.vehicle_number ? `<div class="compliance-sub"><strong>Vehicle:</strong> ${escapeHTML(alert.vehicle_number)}</div>` : ''}
            </div>
        `;
    }).join('');
}

/**
 * Fetch and render financial audit log list inside dashboard
 */
async function loadAuditLogs() {
    const container = document.getElementById('auditLogsContainer');
    const card = document.getElementById('adminAuditLogsCard');
    if (!container || !card) return;
    
    const activeRole = localStorage.getItem('hks_user_role') || 'Customer';
    if (activeRole !== 'Admin/Owner') {
        card.classList.add('d-none');
        return;
    }
    
    card.classList.remove('d-none');
    try {
        const response = await fetch('/api/audit-logs');
        const logs = await response.json();
        if (!response.ok) throw new Error(logs.error || 'Failed to load audit logs');
        
        if (!logs || logs.length === 0) {
            container.innerHTML = `<div class="p-3 text-center text-muted small">No audit logs recorded yet.</div>`;
            return;
        }
        
        container.innerHTML = logs.map(log => {
            return `
                <div class="list-group-item p-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-bold text-navy">INV-#${log.invoice_id}</span>
                        <span class="badge bg-light text-dark">${log.timestamp}</span>
                    </div>
                    <div class="mb-1 text-secondary">
                        Field <strong>${escapeHTML(log.field_name)}</strong> changed:
                    </div>
                    <div class="d-flex align-items-center gap-2 small">
                        <span class="text-danger text-decoration-line-through">${escapeHTML(log.old_value)}</span>
                        <i class="bi bi-arrow-right"></i>
                        <span class="text-success fw-semibold">${escapeHTML(log.new_value)}</span>
                    </div>
                    <div class="mt-2 text-muted" style="font-size: 0.75rem;">
                        By: <strong>${escapeHTML(log.username)}</strong> (${escapeHTML(log.role)})
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error(err);
        container.innerHTML = `<div class="p-3 text-center text-danger small">Error loading logs.</div>`;
    }
}

function showTableLoading() {
    const tableBody = document.getElementById('invoiceTableBody');
    if (!tableBody) return;
    tableBody.innerHTML = `
        <tr>
            <td colspan="10" class="py-5 text-center">
                <div class="loading-overlay">
                    <div class="spinner-custom me-3"></div>
                    <span class="text-muted fw-semibold">Loading shipment records...</span>
                </div>
            </td>
        </tr>
    `;
}

function showNotification(type, message) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toastId = 'toast_' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0 shadow" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${escapeHTML(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = document.getElementById(toastId);
    const bsToast = new bootstrap.Toast(toastElement, { delay: 6000 });
    bsToast.show();
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function formatCurrency(value) {
    return Number(value).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function escapeHTML(str) {
    if (!str) return '';
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
