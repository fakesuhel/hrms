/**
 * Indian Standard Time (IST) Utility Functions
 * Common utilities for handling IST time formatting across the application
 */

// Global user data storage
window.currentUserData = null;

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
 * @param {string} dateTimeString - ISO datetime string
 * @returns {string} Formatted datetime in IST
 */
function formatISTDateTime(dateTimeString) {
    if (!dateTimeString) return 'N/A';
    
    const date = new Date(dateTimeString);
    // Convert to IST (UTC+5:30) manually
    const istDate = new Date(date.getTime() + (5.5 * 60 * 60 * 1000) - (date.getTimezoneOffset() * 60 * 1000));
    
    const day = istDate.getDate();
    const month = istDate.toLocaleDateString('en-US', { month: 'short' });
    const year = istDate.getFullYear();
    
    let hours = istDate.getHours();
    const minutes = istDate.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'pm' : 'am';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    
    return `${day} ${month} ${year}, ${hours}:${minutes} ${ampm} IST`;
}

/**
 * Format time string to IST (time only)
 * @param {string} dateTimeString - ISO datetime string
 * @returns {string} Formatted time in IST
 */
function formatISTTime(dateTimeString) {
    if (!dateTimeString) return 'N/A';
    
    const date = new Date(dateTimeString);
    const istDate = new Date(date.getTime() + (5.5 * 60 * 60 * 1000) - (date.getTimezoneOffset() * 60 * 1000));
    const hours = istDate.getHours().toString().padStart(2, '0');
    const minutes = istDate.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes} IST`;
}

/**
 * Format date string to IST (date only)
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date in IST
 */
function formatISTDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
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
 * Load current user data and store globally
 * @returns {Promise<Object>} User data object
 */
async function loadUserData() {
    try {
        const token = localStorage.getItem('bhoomitechzone_token');
        if (!token) {
            throw new Error('No authentication token found');
        }
        
        const response = await fetch('/users/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('bhoomitechzone_token');
                window.location.href = '/static/login.html';
                return null;
            }
            throw new Error('Failed to fetch user data');
        }
        
        const userData = await response.json();
        
        // Store user data globally
        window.currentUserData = userData;
        
        console.log(`User loaded: ${userData.full_name || userData.username} (${userData.role}) at ${formatISTDateTime(new Date())}`);
        
        return userData;
        
    } catch (error) {
        console.error('Error loading user data:', error);
        throw error;
    }
}

/**
 * Update user display elements on the page
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
        element.textContent = userData.position || userData.role || 'Employee';
    });
    
    // Update user initials
    const userInitialsElements = document.querySelectorAll('#userInitials, .user-initials');
    const initials = getInitials(userData.full_name || userData.username);
    userInitialsElements.forEach(element => {
        element.textContent = initials;
    });
    
    // Update email displays
    const emailElements = document.querySelectorAll('.user-email');
    emailElements.forEach(element => {
        element.textContent = userData.email || '';
    });
    
    // Update time display with user info
    const userTimeElements = document.querySelectorAll('#userTimeDisplay, .user-time-display');
    userTimeElements.forEach(element => {
        const updateTimeDisplay = () => {
            const currentTime = getCurrentISTTime();
            const timeString = currentTime.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Asia/Kolkata'
            });
            element.textContent = `${timeString} IST - ${userData.full_name || userData.username}`;
        };
        
        // Update immediately and then every minute
        updateTimeDisplay();
        
        // Clear any existing interval and set a new one
        if (element._timeInterval) {
            clearInterval(element._timeInterval);
        }
        element._timeInterval = setInterval(updateTimeDisplay, 60000);
    });
}

/**
 * Show toast notification
 * @param {string} message - Message to show
 * @param {string} type - Type of toast (success, error, info)
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
        console.log(`Toast (${type}):`, message);
    }
}

/**
 * Initialize IST utilities and user data for any page
 * Call this function in DOMContentLoaded for consistent setup
 */
async function initializeISTAndUserData() {
    try {
        // Check authentication
        const token = localStorage.getItem('bhoomitechzone_token');
        if (!token) {
            window.location.href = '/static/login.html';
            return;
        }
        
        // Load user data
        const userData = await loadUserData();
        if (userData) {
            updateUserDisplay(userData);
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
            element.textContent = currentDateTime.toLocaleDateString('en-IN', dateOptions);
        });
        
        console.log(`Page initialized at ${formatISTDateTime(new Date())} for user: ${userData ? (userData.full_name || userData.username) : 'Unknown'}`);
        
        return userData;
        
    } catch (error) {
        console.error('Error initializing IST and user data:', error);
        showToast('Error loading user data. Please refresh the page.', 'error');
        throw error;
    }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCurrentISTTime,
        formatISTDateTime,
        formatISTTime,
        formatISTDate,
        getISTDateString,
        formatDateInputIST,
        getInitials,
        loadUserData,
        updateUserDisplay,
        showToast,
        initializeISTAndUserData
    };
}
