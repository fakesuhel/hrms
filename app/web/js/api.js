/**
 * API Integration Module for Bhoomi TechZone HRMS
 * Current Date: 2025-06-11 07:02:48
 * User: soherucontinue
 */

// Base API URL - relative paths for same-domain deployment
const API_BASE_URL = '';

// Authentication token storage
let authToken = localStorage.getItem('bhoomitechzone_token');
let currentUser = null;

/**
 * Handle API requests with automatic token management
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {Object} options - Fetch options
 * @returns {Promise} - API response promise
 */
async function apiRequest(endpoint, options = {}) {
    // Set default headers
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    // Add auth token if available
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    // Prepare request
    const requestOptions = {
        ...options,
        headers
    };

    try {
        // Make request
        const response = await fetch(`${API_BASE_URL}${endpoint}`, requestOptions);
        
        // Handle unauthorized errors (expired token)
        if (response.status === 401) {
            authToken = null;
            localStorage.removeItem('bhoomitechzone_token');
            window.location.href = '/app/login';
            return;
        }
        
        // Handle other error responses
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.status}`);
        }

        // Return successful response
        if (response.status === 204) {
            return null; // No content
        }
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

/**
 * Authentication API functions
 */
const AuthAPI = {
    // Login user
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE_URL}/users/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Login failed. Please check your credentials.');
        }
        
        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('bhoomitechzone_token', authToken);
        
        // Get user details
        await this.getCurrentUser();
        return currentUser;
    },
    
    // Logout user
    logout() {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('bhoomitechzone_token');
        window.location.href = '/app/login';
    },
    
    // Get current user details
    async getCurrentUser() {
        if (!authToken) {
            return null;
        }
        
        try {
            currentUser = await apiRequest('/users/me');
            return currentUser;
        } catch (error) {
            console.error('Error getting current user:', error);
            return null;
        }
    },
    
    // Check if user is authenticated
    isAuthenticated() {
        return !!authToken;
    },
    
    // Get current user data
    getUser() {
        return currentUser;
    }
};

/**
 * Attendance API functions
 */
const AttendanceAPI = {
    // Check in
    async checkIn(location = '', note = '') {
        const userId = currentUser?._id;
        if (!userId) throw new Error('User not authenticated');
        
        const today = new Date();
        const checkInData = {
            date: today.toISOString().split('T')[0],
            check_in_location: location,
            check_in_note: note
        };
        
        return await apiRequest('/attendance/check-in', {
            method: 'POST',
            body: JSON.stringify(checkInData)
        });
    },
    
    // Check out
    async checkOut(summary = '', location = '', note = '') {
        const checkOutData = {
            check_out_location: location,
            check_out_note: note,
            work_summary: summary
        };
        
        return await apiRequest('/attendance/check-out', {
            method: 'POST',
            body: JSON.stringify(checkOutData)
        });
    },
    
    // Get today's attendance
    async getTodayStatus() {
        try {
            const today = new Date().toISOString().split('T')[0];
            const response = await apiRequest(`/attendance/history?start_date=${today}&end_date=${today}`);
            
            return response.length > 0 ? response[0] : null;
        } catch (error) {
            console.error('Error getting attendance status:', error);
            return null;
        }
    },
    
    // Get attendance history
    async getHistory(startDate, endDate) {
        const start = startDate.toISOString().split('T')[0];
        const end = endDate.toISOString().split('T')[0];
        
        return await apiRequest(`/attendance/history?start_date=${start}&end_date=${end}`);
    },
    
    // Get team attendance (for managers/leads)
    async getTeamAttendance(date = new Date()) {
        const forDate = date.toISOString().split('T')[0];
        return await apiRequest(`/attendance/team?for_date=${forDate}`);
    },
    
    // Get attendance statistics
    async getStats(startDate, endDate) {
        const start = startDate.toISOString().split('T')[0];
        const end = endDate.toISOString().split('T')[0];
        
        return await apiRequest(`/attendance/stats?start_date=${start}&end_date=${end}`);
    }
};

/**
 * Projects API functions
 */
const ProjectsAPI = {
    // Get all active projects
    async getActiveProjects(page = 1, size = 10) {
        return await apiRequest(`/projects?page=${page}&size=${size}`);
    },
    
    // Get user's projects
    async getUserProjects() {
        return await apiRequest('/projects/user');
    },
    
    // Get project by ID
    async getProject(id) {
        return await apiRequest(`/projects/${id}`);
    },
    
    // Create new project (managers/leads only)
    async createProject(projectData) {
        return await apiRequest('/projects/', {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
    },
    
    // Update project
    async updateProject(id, projectData) {
        return await apiRequest(`/projects/${id}`, {
            method: 'PUT',
            body: JSON.stringify(projectData)
        });
    },
    
    // Add milestone to project
    async addMilestone(projectId, milestoneData) {
        return await apiRequest(`/projects/${projectId}/milestones`, {
            method: 'POST',
            body: JSON.stringify(milestoneData)
        });
    },
    
    // Update milestone status
    async updateMilestoneStatus(projectId, milestoneTitle, status, completionDate = null) {
        let url = `/projects/${projectId}/milestones/${encodeURIComponent(milestoneTitle)}?status=${status}`;
        
        if (completionDate) {
            url += `&completion_date=${completionDate.toISOString().split('T')[0]}`;
        }
        
        return await apiRequest(url, { method: 'PUT' });
    }
};

/**
 * Daily Reports API functions
 */
const ReportsAPI = {
    // Get today's report
    async getTodayReport() {
        return await apiRequest('/daily-reports/today');
    },
    
    // Create new report
    async createReport(reportData) {
        return await apiRequest('/daily-reports/', {
            method: 'POST',
            body: JSON.stringify(reportData)
        });
    },
    
    // Update report
    async updateReport(reportId, reportData) {
        return await apiRequest(`/daily-reports/${reportId}`, {
            method: 'PUT',
            body: JSON.stringify(reportData)
        });
    },
    
    // Get user reports for date range
    async getUserReports(startDate, endDate) {
        const start = startDate.toISOString().split('T')[0];
        const end = endDate.toISOString().split('T')[0];
        
        return await apiRequest(`/daily-reports?start_date=${start}&end_date=${end}`);
    },
    
    // Get team reports for today (managers/leads only)
    async getTeamReports() {
        return await apiRequest('/daily-reports/team/today');
    },
    
    // Get project reports
    async getProjectReports(projectId, startDate, endDate) {
        const start = startDate.toISOString().split('T')[0];
        const end = endDate.toISOString().split('T')[0];
        
        return await apiRequest(`/daily-reports/project/${projectId}?start_date=${start}&end_date=${end}`);
    },
    
    // Get report statistics
    async getStats(startDate, endDate) {
        const start = startDate.toISOString().split('T')[0];
        const end = endDate.toISOString().split('T')[0];
        
        return await apiRequest(`/daily-reports/stats/personal?start_date=${start}&end_date=${end}`);
    }
};

/**
 * Leave Requests API functions
 */
const LeaveAPI = {
    // Create leave request
    async createLeaveRequest(leaveData) {
        return await apiRequest('/leave-requests/', {
            method: 'POST',
            body: JSON.stringify(leaveData)
        });
    },
    
    // Get user leave requests
    async getUserLeaveRequests(status = null) {
        let url = '/leave-requests/';
        if (status) {
            url += `?status=${status}`;
        }
        return await apiRequest(url);
    },
    
    // Get pending approvals (managers/leads only)
    async getPendingApprovals() {
        return await apiRequest('/leave-requests/pending-approval');
    },
    
    // Get leave balance
    async getLeaveBalance() {
        return await apiRequest('/leave-requests/balance');
    },
    
    // Get leave request by ID
    async getLeaveRequest(id) {
        return await apiRequest(`/leave-requests/${id}`);
    },
    
    // Update leave request
    async updateLeaveRequest(id, leaveData) {
        return await apiRequest(`/leave-requests/${id}`, {
            method: 'PUT',
            body: JSON.stringify(leaveData)
        });
    },
    
    // Approve/reject leave request
    async processLeave(id, status, comments = '') {
        const approvalData = {
            status,
            approver_comments: comments
        };
        
        return await apiRequest(`/leave-requests/${id}/approve`, {
            method: 'POST',
            body: JSON.stringify(approvalData)
        });
    },
    
    // Cancel leave request
    async cancelLeave(id) {
        return await apiRequest(`/leave-requests/${id}/cancel`, {
            method: 'POST'
        });
    }
};

/**
 * Performance Reviews API functions
 */
const PerformanceAPI = {
    // Create performance review (managers/leads only)
    async createReview(reviewData) {
        return await apiRequest('/performance-reviews/', {
            method: 'POST',
            body: JSON.stringify(reviewData)
        });
    },
    
    // Get user's performance reviews
    async getUserReviews() {
        return await apiRequest('/performance-reviews/');
    },
    
    // Get reviews conducted by current user (managers/leads only)
    async getConductedReviews(status = null) {
        let url = '/performance-reviews/conducting';
        if (status) {
            url += `?status=${status}`;
        }
        return await apiRequest(url);
    },
    
    // Get team reviews for a period (managers/leads only)
    async getTeamReviews(period) {
        return await apiRequest(`/performance-reviews/team/${period}`);
    },
    
    // Get performance statistics
    async getPerformanceStats(periods = 4) {
        return await apiRequest(`/performance-reviews/stats?periods=${periods}`);
    },
    
    // Get review by ID
    async getReview(id) {
        return await apiRequest(`/performance-reviews/${id}`);
    },
    
    // Update review
    async updateReview(id, reviewData) {
        return await apiRequest(`/performance-reviews/${id}`, {
            method: 'PUT',
            body: JSON.stringify(reviewData)
        });
    },
    
    // Acknowledge review (employee)
    async acknowledgeReview(id, comments = '') {
        const ackData = { user_comments: comments };
        
        return await apiRequest(`/performance-reviews/${id}/acknowledge`, {
            method: 'POST',
            body: JSON.stringify(ackData)
        });
    }
};

// Export the API modules
const API = {
    auth: AuthAPI,
    attendance: AttendanceAPI,
    projects: ProjectsAPI,
    reports: ReportsAPI,
    leave: LeaveAPI,
    performance: PerformanceAPI
};

// Check authentication on page load
(async function() {
    if (authToken) {
        try {
            await AuthAPI.getCurrentUser();
            console.log(`Authentication check completed at: ${new Date().toISOString()}`);
            console.log(`Current user: ${currentUser ? currentUser.username : 'None'}`);
        } catch (error) {
            console.warn('Invalid auth token, clearing session...');
            AuthAPI.logout();
        }
    }
})();