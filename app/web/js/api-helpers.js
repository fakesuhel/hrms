/**
 * Enhanced API Helper Utilities
 * Additional utility functions for the frontend API integration
 */

class ApiHelpers {
    /**
     * Format currency values
     */
    static formatCurrency(amount, currency = 'USD') {
        if (amount === null || amount === undefined) return '$0.00';
        
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(amount);
    }

    /**
     * Format dates in a user-friendly way
     */
    static formatDate(dateString, options = {}) {
        if (!dateString) return 'N/A';
        
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        
        const formatOptions = { ...defaultOptions, ...options };
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', formatOptions);
        } catch (error) {
            console.error('Error formatting date:', error);
            return 'Invalid Date';
        }
    }

    /**
     * Format time from datetime string
     */
    static formatTime(dateTimeString) {
        if (!dateTimeString) return 'N/A';
        
        try {
            const date = new Date(dateTimeString);
            return date.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
        } catch (error) {
            console.error('Error formatting time:', error);
            return 'Invalid Time';
        }
    }

    /**
     * Format relative time (e.g., "2 hours ago")
     */
    static formatRelativeTime(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);
            
            if (diffInSeconds < 60) return 'Just now';
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
            if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
            
            return this.formatDate(dateString);
        } catch (error) {
            console.error('Error formatting relative time:', error);
            return 'Invalid Date';
        }
    }

    /**
     * Debounce function for search inputs
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function for scroll events
     */
    static throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Handle API errors with user-friendly messages
     */
    static handleApiError(error, customMessage = null) {
        console.error('API Error:', error);
        
        let message = customMessage || 'An error occurred. Please try again.';
        
        if (error.response) {
            // Server responded with error status
            const status = error.response.status;
            const data = error.response.data;
            
            switch (status) {
                case 401:
                    message = 'You are not authorized. Please log in again.';
                    // Redirect to login
                    setTimeout(() => {
                        window.location.href = '/login.html';
                    }, 2000);
                    break;
                case 403:
                    message = 'You do not have permission to perform this action.';
                    break;
                case 404:
                    message = 'The requested resource was not found.';
                    break;
                case 422:
                    message = data.detail || 'Invalid data provided.';
                    break;
                case 500:
                    message = 'Server error. Please try again later.';
                    break;
                default:
                    message = data.detail || data.message || message;
            }
        } else if (error.request) {
            // Network error
            message = 'Network error. Please check your connection.';
        }
        
        this.showNotification(message, 'error');
        return message;
    }

    /**
     * Show notification to user
     */
    static showNotification(message, type = 'info', duration = 5000) {
        // Remove existing notifications
        const existing = document.querySelectorAll('.api-notification');
        existing.forEach(el => el.remove());
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${this.getBootstrapAlertClass(type)} alert-dismissible fade show api-notification`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }
    }

    /**
     * Convert notification type to Bootstrap alert class
     */
    static getBootstrapAlertClass(type) {
        const mapping = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return mapping[type] || 'info';
    }

    /**
     * Validate email format
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Validate phone number format
     */
    static isValidPhone(phone) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
    }

    /**
     * Generate random ID
     */
    static generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * Deep clone object
     */
    static deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    }

    /**
     * Safely get nested object property
     */
    static getNestedProperty(obj, path, defaultValue = null) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : defaultValue;
        }, obj);
    }

    /**
     * Format file size
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Capitalize first letter of each word
     */
    static titleCase(str) {
        return str.replace(/\w\S*/g, (txt) => {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    }

    /**
     * Convert snake_case to Title Case
     */
    static snakeToTitle(str) {
        return this.titleCase(str.replace(/_/g, ' '));
    }

    /**
     * Truncate text with ellipsis
     */
    static truncate(text, maxLength = 100) {
        if (!text || text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }

    /**
     * Create loading spinner element
     */
    static createLoadingSpinner(size = 'normal') {
        const spinner = document.createElement('div');
        const spinnerClass = size === 'small' ? 'spinner-border-sm' : '';
        
        spinner.innerHTML = `
            <div class="d-flex justify-content-center align-items-center p-3">
                <div class="spinner-border ${spinnerClass}" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        return spinner;
    }

    /**
     * Show loading state in container
     */
    static showLoading(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="d-flex flex-column justify-content-center align-items-center p-4">
                <div class="spinner-border mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-muted">${message}</p>
            </div>
        `;
    }

    /**
     * Show empty state in container
     */
    static showEmptyState(containerId, message = 'No data available', actionButton = null) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let buttonHtml = '';
        if (actionButton) {
            buttonHtml = `
                <button class="btn btn-primary mt-3" onclick="${actionButton.onClick}">
                    ${actionButton.text}
                </button>
            `;
        }
        
        container.innerHTML = `
            <div class="d-flex flex-column justify-content-center align-items-center p-4">
                <div class="text-muted mb-3" style="font-size: 3rem;">📭</div>
                <p class="text-muted">${message}</p>
                ${buttonHtml}
            </div>
        `;
    }

    /**
     * Scroll to top of page smoothly
     */
    static scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    /**
     * Copy text to clipboard
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard!', 'success', 2000);
            return true;
        } catch (err) {
            console.error('Failed to copy text: ', err);
            this.showNotification('Failed to copy to clipboard', 'error', 2000);
            return false;
        }
    }

    /**
     * Download data as file
     */
    static downloadAsFile(data, filename, type = 'application/json') {
        const blob = new Blob([data], { type });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }

    /**
     * Parse URL parameters
     */
    static getUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    }

    /**
     * Update URL without page reload
     */
    static updateUrl(params, replaceState = false) {
        const url = new URL(window.location);
        Object.entries(params).forEach(([key, value]) => {
            if (value === null || value === undefined || value === '') {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, value);
            }
        });
        
        if (replaceState) {
            window.history.replaceState({}, '', url);
        } else {
            window.history.pushState({}, '', url);
        }
    }

    /**
     * Check if user has permission
     */
    static hasPermission(requiredPermission, userPermissions = null) {
        if (!userPermissions) {
            // Get from global user object or current user
            const currentUser = window.currentUser || window.hrmsApi?.currentUser;
            userPermissions = currentUser?.permissions || [];
        }
        
        if (Array.isArray(userPermissions)) {
            return userPermissions.includes(requiredPermission);
        }
        
        return false;
    }

    /**
     * Check if user has role
     */
    static hasRole(requiredRole, userRoles = null) {
        if (!userRoles) {
            const currentUser = window.currentUser || window.hrmsApi?.currentUser;
            userRoles = currentUser?.roles || [];
        }
        
        if (Array.isArray(userRoles)) {
            return userRoles.includes(requiredRole);
        }
        
        return false;
    }

    /**
     * Hide/show elements based on permissions
     */
    static applyPermissionBasedVisibility() {
        const elements = document.querySelectorAll('[data-permission]');
        elements.forEach(element => {
            const requiredPermission = element.getAttribute('data-permission');
            if (!this.hasPermission(requiredPermission)) {
                element.style.display = 'none';
            }
        });

        const roleElements = document.querySelectorAll('[data-role]');
        roleElements.forEach(element => {
            const requiredRole = element.getAttribute('data-role');
            if (!this.hasRole(requiredRole)) {
                element.style.display = 'none';
            }
        });
    }

    /**
     * Setup automatic permission-based visibility on page load
     */
    static initializePermissionSystem() {
        document.addEventListener('DOMContentLoaded', () => {
            this.applyPermissionBasedVisibility();
        });
    }

    /**
     * Format percentage
     */
    static formatPercentage(value, decimals = 1) {
        if (value === null || value === undefined) return '0%';
        return `${parseFloat(value).toFixed(decimals)}%`;
    }

    /**
     * Calculate percentage
     */
    static calculatePercentage(part, total) {
        if (!total || total === 0) return 0;
        return (part / total) * 100;
    }

    /**
     * Get status badge HTML
     */
    static getStatusBadge(status, colorMap = {}) {
        const defaultColors = {
            'active': 'success',
            'inactive': 'secondary',
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'completed': 'success',
            'in_progress': 'primary',
            'cancelled': 'danger'
        };
        
        const colors = { ...defaultColors, ...colorMap };
        const color = colors[status] || 'secondary';
        
        return `<span class="badge bg-${color}">${this.snakeToTitle(status)}</span>`;
    }

    /**
     * Export data to CSV
     */
    static exportToCSV(data, filename = 'export.csv') {
        if (!data || data.length === 0) {
            this.showNotification('No data to export', 'warning');
            return;
        }

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => {
                const value = row[header];
                // Escape commas and quotes in CSV
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value || '';
            }).join(','))
        ].join('\n');

        this.downloadAsFile(csvContent, filename, 'text/csv');
    }
}

// Initialize permission system
ApiHelpers.initializePermissionSystem();

// Make ApiHelpers available globally
window.ApiHelpers = ApiHelpers;
