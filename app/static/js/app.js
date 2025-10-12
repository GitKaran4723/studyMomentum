// Goal Tracker Application JavaScript

// Initialize Material Design Components
document.addEventListener('DOMContentLoaded', function() {
    // Auto-initialize all MDC components
    mdc.autoInit();
    
    // Initialize navigation drawer
    const drawer = document.querySelector('.mdc-drawer');
    const topAppBar = document.querySelector('.mdc-top-app-bar');
    const menuButton = document.getElementById('menu-button');
    
    if (drawer && menuButton) {
        const drawerComponent = new mdc.drawer.MDCDrawer(drawer);
        const topAppBarComponent = new mdc.topAppBar.MDCTopAppBar(topAppBar);
        
        menuButton.addEventListener('click', () => {
            drawerComponent.open = !drawerComponent.open;
        });
    }
    
    // Initialize snackbars for flash messages
    const snackbars = document.querySelectorAll('.mdc-snackbar');
    snackbars.forEach(snackbar => {
        const snackbarComponent = new mdc.snackbar.MDCSnackbar(snackbar);
        snackbarComponent.open();
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            snackbarComponent.close();
        }, 5000);
    });
    
    // Initialize data tables
    const dataTables = document.querySelectorAll('.mdc-data-table');
    dataTables.forEach(table => {
        new mdc.dataTable.MDCDataTable(table);
    });
    
    // Initialize text fields
    const textFields = document.querySelectorAll('.mdc-text-field');
    textFields.forEach(textField => {
        new mdc.textField.MDCTextField(textField);
    });
    
    // Initialize select fields
    const selects = document.querySelectorAll('.mdc-select');
    selects.forEach(select => {
        new mdc.select.MDCSelect(select);
    });
    
    // Initialize buttons
    const buttons = document.querySelectorAll('.mdc-button');
    buttons.forEach(button => {
        new mdc.ripple.MDCRipple(button);
    });
    
    // Initialize checkboxes
    const checkboxes = document.querySelectorAll('.mdc-checkbox');
    checkboxes.forEach(checkbox => {
        new mdc.checkbox.MDCCheckbox(checkbox);
    });
    
    // Initialize cards
    const cards = document.querySelectorAll('.mdc-card');
    cards.forEach(card => {
        new mdc.ripple.MDCRipple(card);
    });
    
    // Service Worker Registration for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('Service Worker registered successfully');
            })
            .catch(error => {
                console.log('Service Worker registration failed:', error);
            });
    }
    
    // Initialize app features
    initializeApp();
});

function initializeApp() {
    // Dashboard data refresh
    if (document.getElementById('dashboard')) {
        refreshDashboardData();
        setInterval(refreshDashboardData, 60000); // Refresh every minute
    }
    
    // Auto-save form data
    initializeAutoSave();
    
    // Handle offline status
    handleOfflineStatus();
    
    // Initialize notifications
    initializeNotifications();
}

// Dashboard data refresh
function refreshDashboardData() {
    fetch('/api/dashboard-data')
        .then(response => response.json())
        .then(data => {
            updateDashboardMetrics(data);
        })
        .catch(error => {
            console.log('Failed to refresh dashboard data:', error);
        });
}

function updateDashboardMetrics(data) {
    const todayData = data.today;
    
    // Update metric cards
    const totalTasksElement = document.getElementById('total-tasks-today');
    const completedTasksElement = document.getElementById('completed-tasks-today');
    const scoreElement = document.getElementById('score-today');
    
    if (totalTasksElement) totalTasksElement.textContent = todayData.total_tasks;
    if (completedTasksElement) completedTasksElement.textContent = todayData.completed_tasks;
    if (scoreElement) scoreElement.textContent = todayData.total_score.toFixed(2);
    
    // Update progress bar
    const progressBar = document.getElementById('today-progress');
    if (progressBar && todayData.total_tasks > 0) {
        const percentage = (todayData.completed_tasks / todayData.total_tasks) * 100;
        progressBar.style.width = percentage + '%';
    }
}

// Auto-save functionality
function initializeAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        const formId = form.getAttribute('data-autosave');
        
        // Load saved data
        const savedData = localStorage.getItem(`autosave_${formId}`);
        if (savedData) {
            const data = JSON.parse(savedData);
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = data[key];
                }
            });
        }
        
        // Save data on input
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                const formData = new FormData(form);
                const data = {};
                for (let [key, value] of formData.entries()) {
                    data[key] = value;
                }
                localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));
            });
        });
        
        // Clear saved data on successful submit
        form.addEventListener('submit', () => {
            localStorage.removeItem(`autosave_${formId}`);
        });
    });
}

// Offline status handling
function handleOfflineStatus() {
    function updateOnlineStatus() {
        const statusElement = document.getElementById('offline-indicator');
        
        if (!navigator.onLine) {
            if (!statusElement) {
                const indicator = document.createElement('div');
                indicator.id = 'offline-indicator';
                indicator.className = 'mdc-snackbar mdc-snackbar--open';
                indicator.innerHTML = `
                    <div class="mdc-snackbar__surface" style="background-color: #ff9800;">
                        <div class="mdc-snackbar__label">You are offline. Some features may not work.</div>
                    </div>
                `;
                document.body.appendChild(indicator);
            }
        } else {
            if (statusElement) {
                statusElement.remove();
            }
        }
    }
    
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
}

// Notification system
function initializeNotifications() {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Utility functions
function showSnackbar(message, type = 'info') {
    const snackbar = document.createElement('div');
    snackbar.className = `mdc-snackbar mdc-snackbar--open flash-${type}`;
    snackbar.innerHTML = `
        <div class="mdc-snackbar__surface">
            <div class="mdc-snackbar__label">${message}</div>
            <div class="mdc-snackbar__actions">
                <button type="button" class="mdc-icon-button mdc-snackbar__dismiss material-icons">close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(snackbar);
    
    const snackbarComponent = new mdc.snackbar.MDCSnackbar(snackbar);
    snackbarComponent.open();
    
    setTimeout(() => {
        snackbarComponent.close();
        setTimeout(() => {
            snackbar.remove();
        }, 300);
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(timeString) {
    if (!timeString) return '';
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

// API helper functions
function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// Task management functions
function completeTask(taskId) {
    const data = {
        completed: true,
        enthusiasm_score: null, // Will be prompted
        completion_date: new Date().toISOString().split('T')[0]
    };
    
    // Show completion dialog
    showTaskCompletionDialog(taskId, data);
}

function showTaskCompletionDialog(taskId, data) {
    const dialog = document.createElement('div');
    dialog.className = 'mdc-dialog';
    dialog.innerHTML = `
        <div class="mdc-dialog__container">
            <div class="mdc-dialog__surface">
                <h2 class="mdc-dialog__title">Complete Task</h2>
                <div class="mdc-dialog__content">
                    <div class="mdc-text-field mdc-text-field--outlined">
                        <input type="number" class="mdc-text-field__input" id="enthusiasm-score" min="0" max="10" placeholder="0-10">
                        <div class="mdc-notched-outline">
                            <div class="mdc-notched-outline__leading"></div>
                            <div class="mdc-notched-outline__notch">
                                <label for="enthusiasm-score" class="mdc-floating-label">Enthusiasm Score (0-10)</label>
                            </div>
                            <div class="mdc-notched-outline__trailing"></div>
                        </div>
                    </div>
                    <div class="mdc-text-field mdc-text-field--outlined">
                        <input type="number" class="mdc-text-field__input" id="mcq-percent" min="0" max="100" placeholder="0-100">
                        <div class="mdc-notched-outline">
                            <div class="mdc-notched-outline__leading"></div>
                            <div class="mdc-notched-outline__notch">
                                <label for="mcq-percent" class="mdc-floating-label">MCQ Score (%)</label>
                            </div>
                            <div class="mdc-notched-outline__trailing"></div>
                        </div>
                    </div>
                </div>
                <div class="mdc-dialog__actions">
                    <button type="button" class="mdc-button mdc-dialog__button" data-mdc-dialog-action="cancel">
                        <div class="mdc-button__ripple"></div>
                        <span class="mdc-button__label">Cancel</span>
                    </button>
                    <button type="button" class="mdc-button mdc-button--raised mdc-dialog__button" data-mdc-dialog-action="complete">
                        <div class="mdc-button__ripple"></div>
                        <span class="mdc-button__label">Complete</span>
                    </button>
                </div>
            </div>
        </div>
        <div class="mdc-dialog__scrim"></div>
    `;
    
    document.body.appendChild(dialog);
    
    const dialogComponent = new mdc.dialog.MDCDialog(dialog);
    dialogComponent.open();
    
    dialogComponent.listen('MDCDialog:closed', (event) => {
        if (event.detail.action === 'complete') {
            const enthusiasmScore = document.getElementById('enthusiasm-score').value;
            const mcqPercent = document.getElementById('mcq-percent').value;
            
            const completionData = {
                ...data,
                enthusiasm_score: enthusiasmScore ? parseInt(enthusiasmScore) : null,
                mcq_percent: mcqPercent ? parseFloat(mcqPercent) : null
            };
            
            submitTaskCompletion(taskId, completionData);
        }
        dialog.remove();
    });
}

function submitTaskCompletion(taskId, data) {
    apiCall(`/api/tasks/${taskId}/complete`, {
        method: 'POST',
        body: JSON.stringify(data)
    })
    .then(response => {
        showSnackbar('Task completed successfully!', 'success');
        // Refresh the page or update the UI
        location.reload();
    })
    .catch(error => {
        console.error('Error completing task:', error);
        showSnackbar('Failed to complete task', 'error');
    });
}

// Chart initialization (if needed)
function initializeCharts() {
    // Charts will be implemented when analytics page is created
    console.log('Charts initialized');
}