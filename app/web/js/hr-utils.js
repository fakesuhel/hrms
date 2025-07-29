/**
 * HR Department Utility Functions
 * Specific utilities for HR department operations and IST time handling
 */

// Global HR data storage
window.hrData = {
    currentUser: null,
    employees: [],
    payroll: [],
    attendance: [],
    recruitment: []
};

/**
 * Get current time in IST
 * @returns {Date} Current time converted to IST
 */
function getCurrentISTTime() {
    const now = new Date();
    // Convert to IST (UTC+5:30)
    const istOffset = 5.5 * 60 * 60 * 1000; // 5 hours 30 minutes in milliseconds
    const istTime = new Date(now.getTime() + istOffset - (now.getTimezoneOffset() * 60 * 1000));
    return istTime;
}

/**
 * Get current time formatted for display
 * @returns {string} Current time in HH:MM format IST
 */
function getCurrentTimeFormatted() {
    const currentTime = getCurrentISTTime();
    const hours = currentTime.getHours().toString().padStart(2, '0');
    const minutes = currentTime.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes} IST`;
}

/**
 * Convert any date to IST
 * @param {Date} date - Date to convert
 * @returns {Date} Date converted to IST
 */
function convertToIST(date) {
    if (!date) return new Date();
    const istOffset = 5.5 * 60 * 60 * 1000; // 5 hours 30 minutes in milliseconds
    return new Date(date.getTime() + istOffset - (date.getTimezoneOffset() * 60 * 1000));
}

/**
 * Format datetime string to IST with full date and time
 * @param {string|Date} dateTimeString - ISO datetime string or Date object
 * @returns {string} Formatted datetime in IST
 */
function formatISTDateTime(dateTimeString) {
    if (!dateTimeString) return 'N/A';
    
    const date = new Date(dateTimeString);
    if (isNaN(date.getTime())) return 'Invalid Date';
    
    // Convert to IST (UTC+5:30) manually
    const istDate = new Date(date.getTime() + (5.5 * 60 * 60 * 1000) - (date.getTimezoneOffset() * 60 * 1000));
    
    const day = istDate.getDate();
    const month = istDate.toLocaleDateString('en-US', { month: 'short' });
    const year = istDate.getFullYear();
    
    let hours = istDate.getHours();
    const minutes = istDate.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    
    return `${day} ${month} ${year}, ${hours}:${minutes} ${ampm} IST`;
}

/**
 * Format time string to IST (time only)
 * @param {string|Date} dateTimeString - ISO datetime string or Date object
 * @returns {string} Formatted time in IST
 */
function formatISTTime(dateTimeString) {
    if (!dateTimeString) return 'N/A';
    
    const date = new Date(dateTimeString);
    if (isNaN(date.getTime())) return 'Invalid Time';
    
    const istDate = new Date(date.getTime() + (5.5 * 60 * 60 * 1000) - (date.getTimezoneOffset() * 60 * 1000));
    const hours = istDate.getHours().toString().padStart(2, '0');
    const minutes = istDate.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes} IST`;
}

/**
 * Format date string to IST (date only)
 * @param {string|Date} dateString - ISO date string or Date object
 * @returns {string} Formatted date in IST
 */
function formatISTDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid Date';
    
    // Convert to IST (UTC+5:30) manually
    const istDate = new Date(date.getTime() + (5.5 * 60 * 60 * 1000) - (date.getTimezoneOffset() * 60 * 1000));
    
    const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const weekday = weekdays[istDate.getDay()];
    const day = istDate.getDate();
    const month = months[istDate.getMonth()];
    const year = istDate.getFullYear();
    
    return `${weekday}, ${day} ${month} ${year}`;
}

/**
 * Get IST date string in YYYY-MM-DD format
 * @returns {string} Current date in IST as YYYY-MM-DD
 */
function getISTDateString() {
    const istTime = getCurrentISTTime();
    return istTime.toISOString().split('T')[0];
}

/**
 * Format date for HTML input fields (YYYY-MM-DD) in IST
 * @param {Date} date - Date object
 * @returns {string} Date in YYYY-MM-DD format for IST
 */
function formatDateInputIST(date) {
    if (!date) return '';
    
    // Convert to IST first, then get the date part
    const istDate = new Date(date.getTime() + (5.5 * 60 * 60 * 1000) - (date.getTimezoneOffset() * 60 * 1000));
    return istDate.toISOString().split('T')[0];
}

/**
 * Get user initials from full name
 * @param {string} fullName - Full name of the user
 * @returns {string} User initials
 */
function getInitials(fullName) {
    if (!fullName) return 'U';
    const names = fullName.trim().split(' ');
    if (names.length === 1) {
        return names[0].charAt(0).toUpperCase();
    } else {
        return (names[0].charAt(0) + names[names.length - 1].charAt(0)).toUpperCase();
    }
}

/**
 * Load current user data and store globally for HR
 * @returns {Promise<Object>} User data object
 */
async function getCurrentUser() {
    try {
        const token = localStorage.getItem('bhoomitechzone_token');
        if (!token) return null;
        
        const response = await fetch('/users/me', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const userData = await response.json();
            window.hrData.currentUser = userData;
            return userData;
        }
    } catch (error) {
        console.error('Error fetching current user:', error);
    }
    
    // Fallback to localStorage or generic user if API fails
    const username = localStorage.getItem('username') || 'User';
    const names = username.split(/[._-\s]/);
    const fallbackUser = {
        id: 0,
        username: username,
        first_name: names.length > 0 ? names[0] : '',
        last_name: names.length > 1 ? names[1] : '',
        role: localStorage.getItem('user_role') || 'hr',
        position: localStorage.getItem('user_position') || 'HR Team Member'
    };
    window.hrData.currentUser = fallbackUser;
    return fallbackUser;
}

/**
 * Update user display elements on the page for HR
 * @param {Object} userData - User data object
 */
function updateUserDisplay(userData) {
    if (!userData) return;
    
    // Update username displays
    const usernameElements = document.querySelectorAll('#sidebar-username, .user-display-name');
    usernameElements.forEach(element => {
        element.textContent = userData.full_name || userData.username || 'Unknown User';
    });
    
    // Update position/role displays
    const positionElements = document.querySelectorAll('#sidebar-position, .user-position');
    positionElements.forEach(element => {
        element.textContent = userData.position || userData.role || 'HR Team Member';
    });
    
    // Update user initials
    const userInitialsElements = document.querySelectorAll('#userInitials, .user-initials');
    const initials = getInitials(userData.full_name || userData.username);
    userInitialsElements.forEach(element => {
        element.textContent = initials;
    });
    
    // Update time display with user info
    const userTimeElements = document.querySelectorAll('#userTimeDisplay, .user-time-display');
    userTimeElements.forEach(element => {
        const updateTimeDisplay = () => {
            const timeString = getCurrentTimeFormatted();
            element.textContent = `${timeString} - ${userData.username}`;
        };
        
        // Update immediately and then every second
        updateTimeDisplay();
        
        // Clear any existing interval and set a new one
        if (element._timeInterval) {
            clearInterval(element._timeInterval);
        }
        element._timeInterval = setInterval(updateTimeDisplay, 1000);
    });
}

/**
 * Show toast notification for HR pages
 * @param {string} message - Message to show
 * @param {string} type - Type of toast (success, error, info, warning)
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    } else {
        console.log(`HR Toast (${type}):`, message);
    }
}

/**
 * Setup common HR page event listeners
 */
function setupHREventListeners() {
    // Menu toggle
    const menuToggle = document.getElementById('menuToggle');
    const dashboardContainer = document.getElementById('dashboardContainer');
    if (menuToggle && dashboardContainer) {
        menuToggle.addEventListener('click', function() {
            dashboardContainer.classList.toggle('sidebar-hidden');
        });
    }
    
    // User dropdown
    const userMenu = document.getElementById('userMenu');
    const userDropdown = document.getElementById('userDropdown');
    if (userMenu && userDropdown) {
        userMenu.addEventListener('click', function() {
            userDropdown.classList.toggle('active');
        });
        document.addEventListener('click', function(event) {
            if (!userMenu.contains(event.target)) {
                userDropdown.classList.remove('active');
            }
        });
    }
    
    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('bhoomitechzone_token');
            localStorage.removeItem('username');
            localStorage.removeItem('user_role');
            localStorage.removeItem('user_position');
            window.location.href = '/static/login.html';
        });
    }
}

/**
 * Initialize HR page with user data and IST utilities
 * @returns {Promise<Object>} Current user data
 */
async function initializeHRPage() {
    try {
        // Check authentication
        const token = localStorage.getItem('bhoomitechzone_token');
        if (!token) {
            window.location.href = '/static/login.html';
            return;
        }
        
        // Load user data
        const currentUser = await getCurrentUser();
        
        if (currentUser) {
            updateUserDisplay(currentUser);
        }
        
        // Update current date displays with IST
        const currentDateElements = document.querySelectorAll('#currentDate, .current-date');
        const currentDateTime = getCurrentISTTime();
        const dateOptions = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            timeZone: 'Asia/Kolkata'
        };
        
        currentDateElements.forEach(element => {
            element.textContent = currentDateTime.toLocaleDateString('en-IN', dateOptions) + ' (IST)';
        });
        
        // Setup common event listeners
        setupHREventListeners();
        
        console.log(`HR Page initialized at ${formatISTDateTime(new Date())} for user: ${currentUser ? (currentUser.username) : 'Unknown'}`);
        
        return currentUser;
        
    } catch (error) {
        console.error('Error initializing HR page:', error);
        showToast('Error loading page data. Please refresh.', 'error');
        throw error;
    }
}

/**
 * Format currency in Indian Rupees
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    if (typeof amount !== 'number') return '₹0';
    return `₹${amount.toLocaleString('en-IN')}`;
}

/**
 * Calculate working hours between two times
 * @param {string|Date} startTime - Start time
 * @param {string|Date} endTime - End time
 * @returns {string} Formatted working hours
 */
function calculateWorkingHours(startTime, endTime) {
    if (!startTime || !endTime) return '0h 0m';
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    
    if (isNaN(start.getTime()) || isNaN(end.getTime())) return '0h 0m';
    
    const diffMs = end - start;
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${hours}h ${minutes}m`;
}

/**
 * Validate employee data
 * @param {Object} employeeData - Employee data to validate
 * @returns {Object} Validation result with isValid and errors
 */
function validateEmployeeData(employeeData) {
    const errors = [];
    
    if (!employeeData.first_name?.trim()) {
        errors.push('First name is required');
    }
    
    if (!employeeData.last_name?.trim()) {
        errors.push('Last name is required');
    }
    
    if (!employeeData.email?.trim()) {
        errors.push('Email is required');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(employeeData.email)) {
        errors.push('Invalid email format');
    }
    
    if (!employeeData.department?.trim()) {
        errors.push('Department is required');
    }
    
    if (!employeeData.position?.trim()) {
        errors.push('Position is required');
    }
    
    if (!employeeData.join_date) {
        errors.push('Join date is required');
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

/**
 * Generate employee ID
 * @param {string} firstName - First name
 * @param {string} lastName - Last name
 * @param {Date} joinDate - Join date
 * @returns {string} Generated employee ID
 */
function generateEmployeeId(firstName, lastName, joinDate) {
    const year = new Date(joinDate).getFullYear().toString().slice(-2);
    const initials = (firstName.charAt(0) + lastName.charAt(0)).toUpperCase();
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `EMP${year}${initials}${random}`;
}

/**
 * Get status badge class for different statuses
 * @param {string} status - Status value
 * @returns {string} CSS class for badge
 */
function getStatusBadgeClass(status) {
    switch (status?.toLowerCase()) {
        case 'active':
        case 'present':
        case 'approved':
        case 'completed':
        case 'paid':
            return 'badge-success';
        case 'inactive':
        case 'absent':
        case 'rejected':
        case 'cancelled':
            return 'badge-danger';
        case 'pending':
        case 'in_progress':
        case 'processing':
            return 'badge-warning';
        case 'on_leave':
        case 'half_day':
        case 'late':
        case 'review':
            return 'badge-info';
        default:
            return 'badge-secondary';
    }
}

/**
 * Format status text for display
 * @param {string} status - Status value
 * @returns {string} Formatted status text
 */
function formatStatusText(status) {
    if (!status) return 'Unknown';
    
    return status
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}

/**
 * Create a debounced function
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Export data to CSV
 * @param {Array} data - Array of objects to export
 * @param {string} filename - Filename for the CSV
 */
function exportToCSV(data, filename) {
    if (!data || data.length === 0) {
        showToast('No data to export', 'warning');
        return;
    }
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => {
                const value = row[header] || '';
                // Escape commas and quotes
                return typeof value === 'string' && (value.includes(',') || value.includes('"')) 
                    ? `"${value.replace(/"/g, '""')}"` 
                    : value;
            }).join(',')
        )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('Data exported successfully', 'success');
}

// Export functions for use in HR pages
window.hrUtils = {
    getCurrentISTTime,
    getCurrentTimeFormatted,
    convertToIST,
    formatISTDateTime,
    formatISTTime,
    formatISTDate,
    getISTDateString,
    formatDateInputIST,
    getInitials,
    getCurrentUser,
    updateUserDisplay,
    showToast,
    setupHREventListeners,
    initializeHRPage,
    formatCurrency,
    calculateWorkingHours,
    validateEmployeeData,
    generateEmployeeId,
    getStatusBadgeClass,
    formatStatusText,
    debounce,
    exportToCSV
};

console.log('HR Utils loaded successfully');
