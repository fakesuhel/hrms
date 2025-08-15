/**
 * User Manager - Handles user authentication and management
 */
class UserManager {
    static TOKEN_KEY = 'bhoomitechzone_token';
    static API_BASE = '';

    /**
     * Check if user is authenticated
     */
    static isAuthenticated() {
        const token = localStorage.getItem(this.TOKEN_KEY);
        return !!token;
    }

    /**
     * Get the current authentication token
     */
    static getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    /**
     * Login user
     */
    static async login(username, password) {
        try {
            const response = await fetch('/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: username,
                    password: password
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Store the token
                localStorage.setItem(this.TOKEN_KEY, data.access_token);
                
                return { success: true, data: data };
            } else {
                const errorData = await response.json();
                return { 
                    success: false, 
                    error: errorData.detail || 'Login failed' 
                };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { 
                success: false, 
                error: 'Network error. Please try again.' 
            };
        }
    }

    /**
     * Register new user
     */
    static async registerUser(userData) {
        try {
            const response = await fetch('/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            } else {
                const errorData = await response.json();
                return { 
                    success: false, 
                    error: errorData.detail || 'Registration failed' 
                };
            }
        } catch (error) {
            console.error('Registration error:', error);
            return { 
                success: false, 
                error: 'Network error. Please try again.' 
            };
        }
    }

    /**
     * Get current user data
     */
    static async getCurrentUser() {
        try {
            const token = this.getToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch('/users/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                return userData;
            } else {
                throw new Error('Failed to get user data');
            }
        } catch (error) {
            console.error('Get current user error:', error);
            throw error;
        }
    }

    /**
     * Logout user
     */
    static logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        window.location.href = '/app/login';
    }

    /**
     * Get department-specific dashboard URL
     */
    static getDepartmentDashboardUrl(department) {
        if (!department) return '/app/dashboard';
        
        const dept = department.toLowerCase();
        
        if (dept === 'sales') {
            return '/app/sales/dashboard';
        } else if (dept === 'human resources' || dept === 'hr') {
            return '/app/hr/dashboard';
        } else if (dept === 'development') {
            return '/app/it/dashboard';
        }
        
        return '/app/dashboard'; // default fallback
    }

    /**
     * Redirect to appropriate dashboard based on user department
     */
    static async redirectToDepartmentDashboard() {
        try {
            const userData = await this.getCurrentUser();
            const dashboardUrl = this.getDepartmentDashboardUrl(userData.department);
            window.location.href = dashboardUrl;
        } catch (error) {
            console.error('Error redirecting to department dashboard:', error);
            window.location.href = '/app/it/dashboard';
        }
    }

    /**
     * Make authenticated API request
     */
    static async apiRequest(url, options = {}) {
        const token = this.getToken();
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };

        try {
            const response = await fetch(url, mergedOptions);
            
            // If unauthorized, redirect to login
            if (response.status === 401) {
                this.logout();
                return;
            }

            return response;
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }
}

// Make UserManager available globally
window.UserManager = UserManager;

// Debug: Log when UserManager is loaded
console.log('UserManager loaded successfully');
console.log('UserManager methods available:', Object.getOwnPropertyNames(UserManager));
