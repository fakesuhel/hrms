/**
 * Navigation Configuration with Clean URLs
 * Centralized navigation mapping for the entire application
 */

const NavigationConfig = {
    // Dashboard Routes
    dashboards: {
        main: '/app/dashboard',
        management: '/app/dashboard/management',
        sales: '/app/dashboard/sales',
        hr: '/app/dashboard/hr',
        development: '/app/dashboard/development',
        marketing: '/app/dashboard/marketing',
        finance: '/app/dashboard/finance'
    },

    // Department Pages
    departments: {
        sales: {
            dashboard: '/app/dashboard/sales',
            customers: '/app/customers',
            leads: '/app/leads',
            payments: '/app/payments',
            reports: '/app/sales/reports'
        },
        hr: {
            dashboard: '/app/dashboard/hr',
            employees: '/app/employees',
            recruitment: '/app/recruitment',
            policies: '/app/policies',
            reports: '/app/hr/reports'
        },
        development: {
            dashboard: '/app/dashboard/development',
            projects: '/app/projects',
            tasks: '/app/tasks',
            code_reviews: '/app/code-reviews',
            reports: '/app/development/reports'
        },
        marketing: {
            dashboard: '/app/dashboard/marketing',
            campaigns: '/app/campaigns',
            analytics: '/app/marketing/analytics',
            content: '/app/content',
            reports: '/app/marketing/reports'
        },
        finance: {
            dashboard: '/app/dashboard/finance',
            accounting: '/app/accounting',
            budgets: '/app/budgets',
            invoices: '/app/invoices',
            reports: '/app/finance/reports'
        }
    },

    // Common Pages
    common: {
        attendance: '/app/attendance',
        daily_reports: '/app/daily-reports',
        teams: '/app/teams',
        performance_reviews: '/app/performance-reviews',
        leave_requests: '/app/leave-requests',
        settings: '/app/settings',
        profile: '/app/profile',
        profile_details: '/app/profile/details',
        profile_documents: '/app/profile/documents',
        salary: '/app/salary',
        salary_slips: '/app/salary/slips',
        penalties: '/app/penalties'
    },

    // Authentication
    auth: {
        login: '/app/login',
        logout: '/app/logout',
        register: '/app/register'
    },

    // API Endpoints
    api: {
        base: '/api/v1',
        auth: '/users/token',
        users: '/users',
        sales: '/sales',
        hr: '/hr',
        development: '/development'
    },

    /**
     * Get dashboard URL based on user role and department
     * @param {string} role - User role
     * @param {string} department - User department
     * @returns {string} - Dashboard URL
     */
    getDashboardUrl(role, department = '') {
        role = (role || 'employee').toLowerCase();
        department = (department || '').toLowerCase();
        
        // Admin and Director roles
        if (['admin', 'director', 'ceo'].includes(role)) {
            return this.dashboards.management;
        }
        
        // Manager roles - determine by department
        if (['manager', 'team_lead', 'team_leader'].includes(role)) {
            if (department.includes('sales')) {
                return this.dashboards.sales;
            } else if (department.includes('hr') || department.includes('human')) {
                return this.dashboards.hr;
            } else if (department.includes('development') || department.includes('dev') || department.includes('tech')) {
                return this.dashboards.development;
            } else {
                return this.dashboards.main;
            }
        }
        
        // Regular employees - determine by department
        if (department.includes('sales')) {
            return this.dashboards.sales;
        } else if (department.includes('hr') || department.includes('human')) {
            return this.dashboards.hr;
        } else if (department.includes('development') || department.includes('dev') || department.includes('tech')) {
            return this.dashboards.development;
        } else if (department.includes('marketing')) {
            return this.dashboards.marketing;
        } else if (department.includes('finance') || department.includes('accounting')) {
            return this.dashboards.finance;
        } else {
            return this.dashboards.main;
        }
    },

    /**
     * Get department pages for a specific department
     * @param {string} department - Department name
     * @returns {object} - Department pages object
     */
    getDepartmentPages(department) {
        department = (department || '').toLowerCase();
        
        if (department.includes('sales')) {
            return this.departments.sales;
        } else if (department.includes('hr') || department.includes('human')) {
            return this.departments.hr;
        } else if (department.includes('development') || department.includes('dev') || department.includes('tech')) {
            return this.departments.development;
        } else if (department.includes('marketing')) {
            return this.departments.marketing;
        } else if (department.includes('finance') || department.includes('accounting')) {
            return this.departments.finance;
        } else {
            return {};
        }
    },

    /**
     * Navigate to a specific page
     * @param {string} url - URL to navigate to
     * @param {boolean} newTab - Open in new tab
     */
    navigate(url, newTab = false) {
        if (newTab) {
            window.open(url, '_blank');
        } else {
            window.location.href = url;
        }
    },

    /**
     * Get all navigation items for a user based on role and department
     * @param {string} role - User role
     * @param {string} department - User department
     * @returns {object} - Navigation items
     */
    getNavigationItems(role, department = '') {
        const dashboardUrl = this.getDashboardUrl(role, department);
        const departmentPages = this.getDepartmentPages(department);
        
        return {
            dashboard: dashboardUrl,
            department: departmentPages,
            common: this.common,
            profile: {
                main: this.common.profile,
                details: this.common.profile_details,
                documents: this.common.profile_documents
            },
            settings: this.common.settings
        };
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NavigationConfig;
}

// Make available globally
window.NavigationConfig = NavigationConfig;
