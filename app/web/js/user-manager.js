/**
 * User Management Module for Bhoomi TechZone HRMS
 * Current Date: 2025-06-11 06:36:36
 * User: soherufix
 */

/**
 * User Manager for handling user-related operations
 */
const UserManager = {
    // Use relative URLs to work with any port
    apiBaseUrl: '',

    /**
     * Register a new user
     * @param {Object} userData - User registration data
     * @returns {Promise} - API response promise
     */
    async registerUser(userData) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/users/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (!response.ok) {
                let errorMessage = 'Registration failed.';
                if (data.detail) {
                    errorMessage = data.detail;
                }
                throw new Error(errorMessage);
            }

            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    /**
     * Login user and get access token
     * @param {string} username - User's username
     * @param {string} password - User's password
     * @returns {Promise} - API response promise
     */
    async login(username, password) {
        try {
            console.log('UserManager: Starting login process for user:', username);

            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const url = `${this.apiBaseUrl}/users/token`;
            console.log('UserManager: Making request to:', url);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });

            console.log('UserManager: Response status:', response.status);

            const data = await response.json();
            console.log('UserManager: Response data:', data);

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed. Please check your credentials.');
            }

            // Store token in localStorage
            localStorage.setItem('bhoomitechzone_token', data.access_token);
            console.log('UserManager: Login successful, token stored');
            return { success: true, token: data.access_token };
        } catch (error) {
            console.error('UserManager: Login error:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Get current user profile using stored token
     * @returns {Promise} - API response promise with user data
     */
    async getCurrentUser() {
        try {
            const token = localStorage.getItem('bhoomitechzone_token');

            if (!token) {
                throw new Error('Not authenticated');
            }

            const response = await fetch(`${this.apiBaseUrl}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error('Failed to get user data');
            }

            return { success: true, user: data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    /**
     * Logout user by clearing stored token
     */
    logout() {
        localStorage.removeItem('bhoomitechzone_token');
        window.location.href = '/static/login.html';
    },

    /**
     * Check if user is currently authenticated
     * @returns {boolean} - True if authenticated
     */
    isAuthenticated() {
        return !!localStorage.getItem('bhoomitechzone_token');
    },

    /**
     * Update user profile
     * @param {Object} userData - User data to update
     * @returns {Promise} - API response promise
     */
    async updateProfile(userData) {
        try {
            const token = localStorage.getItem('bhoomitechzone_token');

            if (!token) {
                throw new Error('Not authenticated');
            }

            const response = await fetch(`${this.apiBaseUrl}/users/me`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error('Failed to update profile');
            }

            return { success: true, user: data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    /**
     * Get team members (for managers and team leads)
     * @returns {Promise} - API response promise with team members
     */
    async getTeamMembers() {
        try {
            const token = localStorage.getItem('bhoomitechzone_token');

            if (!token) {
                throw new Error('Not authenticated');
            }

            const response = await fetch(`${this.apiBaseUrl}/users/team`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 403) {
                return { success: false, error: 'Not authorized to view team' };
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error('Failed to get team members');
            }

            return { success: true, members: data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
};

// Log current time for tracking
console.log('User Manager loaded at: 2025-06-11 06:36:36');