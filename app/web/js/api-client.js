/**
 * Enhanced API Client for Department-Specific HRMS APIs
 * Provides a comprehensive interface for all department APIs with proper error handling
 */

class HRMSApiClient {
    constructor(baseURL = '', token = null) {
        this.baseURL = baseURL;
        this.token = token || localStorage.getItem('bhoomitechzone_token');
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
        localStorage.setItem('bhoomitechzone_token', token);
    }

    // Get headers with authentication
    getHeaders(additionalHeaders = {}) {
        const headers = { ...this.defaultHeaders, ...additionalHeaders };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(options.headers),
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('bhoomitechzone_token');
                window.location.href = '/static/login.html';
                return;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return await response.text();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Sales API Methods
    // ===============

    // Leads Management
    async createLead(leadData) {
        return this.request('/api/sales/leads', {
            method: 'POST',
            body: JSON.stringify(leadData)
        });
    }

    async getLeads(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/sales/leads?${params}`);
    }

    async getLeadById(leadId) {
        return this.request(`/api/sales/leads/${leadId}`);
    }

    async updateLead(leadId, updateData) {
        return this.request(`/api/sales/leads/${leadId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    async deleteLead(leadId) {
        return this.request(`/api/sales/leads/${leadId}`, {
            method: 'DELETE'
        });
    }

    async addLeadActivity(leadId, activityData) {
        return this.request(`/api/sales/leads/${leadId}/activities`, {
            method: 'POST',
            body: JSON.stringify(activityData)
        });
    }

    async getLeadActivities(leadId) {
        return this.request(`/api/sales/leads/${leadId}/activities`);
    }

    // Customers Management
    async createCustomer(customerData) {
        return this.request('/api/sales/customers', {
            method: 'POST',
            body: JSON.stringify(customerData)
        });
    }

    async getCustomers(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/sales/customers?${params}`);
    }

    async getCustomerById(customerId) {
        return this.request(`/api/sales/customers/${customerId}`);
    }

    async updateCustomer(customerId, updateData) {
        return this.request(`/api/sales/customers/${customerId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    async convertLeadToCustomer(leadId, customerData) {
        return this.request(`/api/sales/leads/${leadId}/convert`, {
            method: 'POST',
            body: JSON.stringify(customerData)
        });
    }

    // Sales Statistics
    async getLeadStats() {
        return this.request('/api/sales/stats/leads');
    }

    async getCustomerStats() {
        return this.request('/api/sales/stats/customers');
    }

    // HR API Methods
    // =============

    // Employee Management
    async getAllEmployees(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/hr/employees?${params}`);
    }

    async getEmployeeById(employeeId) {
        return this.request(`/api/hr/employees/${employeeId}`);
    }

    async updateEmployee(employeeId, updateData) {
        return this.request(`/api/hr/employees/${employeeId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    // Recruitment Management
    async createJobPosting(jobData) {
        return this.request('/api/hr/recruitment/jobs', {
            method: 'POST',
            body: JSON.stringify(jobData)
        });
    }

    async getJobPostings(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/hr/recruitment/jobs?${params}`);
    }

    async getJobPostingById(jobId) {
        return this.request(`/api/hr/recruitment/jobs/${jobId}`);
    }

    async updateJobPosting(jobId, updateData) {
        return this.request(`/api/hr/recruitment/jobs/${jobId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    async getJobApplications(jobId) {
        return this.request(`/api/hr/recruitment/jobs/${jobId}/applications`);
    }

    async updateJobApplication(applicationId, updateData) {
        return this.request(`/api/hr/recruitment/applications/${applicationId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    async scheduleInterview(interviewData) {
        return this.request('/api/hr/recruitment/interviews', {
            method: 'POST',
            body: JSON.stringify(interviewData)
        });
    }

    async getUpcomingInterviews() {
        return this.request('/api/hr/recruitment/interviews/upcoming');
    }

    async updateInterview(interviewId, updateData) {
        return this.request(`/api/hr/recruitment/interviews/${interviewId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    // HR Policies Management
    async createHRPolicy(policyData) {
        return this.request('/api/hr/policies', {
            method: 'POST',
            body: JSON.stringify(policyData)
        });
    }

    async getHRPolicies(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/hr/policies?${params}`);
    }

    async getHRPolicyById(policyId) {
        return this.request(`/api/hr/policies/${policyId}`);
    }

    async updateHRPolicy(policyId, updateData) {
        return this.request(`/api/hr/policies/${policyId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    async acknowledgePolicy(policyId, acknowledgmentData) {
        return this.request(`/api/hr/policies/${policyId}/acknowledge`, {
            method: 'POST',
            body: JSON.stringify(acknowledgmentData)
        });
    }

    async getPendingPolicyAcknowledgments() {
        return this.request('/api/hr/policies/pending');
    }

    // HR Reports
    async getAttendanceReport(startDate, endDate, department = null) {
        const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
        if (department) params.append('department', department);
        return this.request(`/api/hr/reports/attendance?${params}`);
    }

    async getLeaveSummaryReport(year, department = null) {
        const params = new URLSearchParams({ year: year.toString() });
        if (department) params.append('department', department);
        return this.request(`/api/hr/reports/leave-summary?${params}`);
    }

    // Development API Methods
    // ======================

    // Project Management
    async createProject(projectData) {
        return this.request('/api/development/projects', {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
    }

    async getProjects(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/development/projects?${params}`);
    }

    async getProjectById(projectId) {
        return this.request(`/api/development/projects/${projectId}`);
    }

    async updateProject(projectId, updateData) {
        return this.request(`/api/development/projects/${projectId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    async deleteProject(projectId) {
        return this.request(`/api/development/projects/${projectId}`, {
            method: 'DELETE'
        });
    }

    // Task Management
    async addProjectTask(projectId, taskData) {
        return this.request(`/api/development/projects/${projectId}/tasks`, {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    }

    async updateProjectTask(projectId, taskId, taskData) {
        return this.request(`/api/development/projects/${projectId}/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(taskData)
        });
    }

    // Team Management
    async getDevelopmentTeams() {
        return this.request('/api/development/teams');
    }

    async getTeamMembers() {
        return this.request('/api/development/team-members');
    }

    // Development Reports
    async getProjectStats() {
        return this.request('/api/development/stats/projects');
    }

    async getProductivityReport(startDate, endDate, teamMemberId = null) {
        const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
        if (teamMemberId) params.append('team_member_id', teamMemberId);
        return this.request(`/api/development/reports/productivity?${params}`);
    }

    async getProjectStatusReport() {
        return this.request('/api/development/reports/project-status');
    }

    // Utility Methods
    // ==============

    // File upload helper
    async uploadFile(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            headers: this.getHeaders({ 'Content-Type': undefined }) // Let browser set multipart boundary
        });
    }

    // Bulk operations
    async bulkUpdate(endpoint, updates) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify({ updates })
        });
    }

    // Export data
    async exportData(endpoint, format = 'json') {
        const params = new URLSearchParams({ format });
        return this.request(`${endpoint}/export?${params}`);
    }
}

// Global API client instance
window.hrmsApi = new HRMSApiClient();

// Helper functions for common operations
const ApiHelpers = {
    // Format date for API
    formatDate(date) {
        if (date instanceof Date) {
            return date.toISOString().split('T')[0];
        }
        return date;
    },

    // Format datetime for API
    formatDateTime(date) {
        if (date instanceof Date) {
            return date.toISOString();
        }
        return date;
    },

    // Handle API errors with user-friendly messages
    handleApiError(error) {
        console.error('API Error:', error);
        
        const errorMessage = error.message || 'An unexpected error occurred';
        
        // Show toast notification or alert
        if (window.showToast) {
            window.showToast(errorMessage, 'error');
        } else {
            alert(`Error: ${errorMessage}`);
        }
    },

    // Show loading state
    showLoading(element, show = true) {
        if (show) {
            element.classList.add('loading');
            element.disabled = true;
        } else {
            element.classList.remove('loading');
            element.disabled = false;
        }
    },

    // Validate required fields
    validateRequiredFields(data, requiredFields) {
        const missing = requiredFields.filter(field => !data[field]);
        if (missing.length > 0) {
            throw new Error(`Missing required fields: ${missing.join(', ')}`);
        }
        return true;
    },

    // Format currency
    formatCurrency(amount, currency = 'INR') {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },

    // Format numbers
    formatNumber(number, decimals = 0) {
        return new Intl.NumberFormat('en-IN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    },

    // Debounce function for search inputs
    debounce(func, wait) {
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
};

// Make helpers available globally
window.ApiHelpers = ApiHelpers;

// Auto-initialize token from localStorage
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('bhoomitechzone_token');
    if (token) {
        window.hrmsApi.setToken(token);
    }
});
