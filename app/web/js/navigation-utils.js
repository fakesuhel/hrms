/**
 * Navigation Utility Functions
 * Provides clean URL navigation throughout the application
 */

class NavigationUtils {
    constructor() {
        this.baseUrl = window.location.origin;
    }

    /**
     * Convert old static file paths to new clean URLs
     * @param {string} oldPath - Old static file path
     * @returns {string} - New clean URL
     */
    convertToCleanUrl(oldPath) {
        const urlMappings = {
            // Dashboard mappings
            '/static/dashboard.html': '/app/dashboard',
            '/static/departments/management/dashboard.html': '/app/dashboard/management',
            '/static/departments/sales/dashboard.html': '/app/dashboard/sales',
            '/static/departments/hr/dashboard.html': '/app/dashboard/hr',
            '/static/departments/development/dashboard.html': '/app/dashboard/development',
            '/static/departments/marketing/dashboard.html': '/app/dashboard/marketing',
            '/static/departments/finance/dashboard.html': '/app/dashboard/finance',
            
            // Page mappings
            '/static/attendance.html': '/app/attendance',
            '/static/daily-reports.html': '/app/daily-reports',
            '/static/teams.html': '/app/teams',
            '/static/projects.html': '/app/projects',
            '/static/performance-reviews.html': '/app/performance-reviews',
            '/static/leave-requests.html': '/app/leave-requests',
            '/static/settings.html': '/app/settings',
            '/static/login.html': '/app/login',
            
            // Department specific pages
            '/static/departments/sales/customers.html': '/app/customers',
            '/static/departments/sales/leads.html': '/app/leads',
            '/static/departments/hr/employees.html': '/app/employees',
            '/static/departments/hr/recruitment.html': '/app/recruitment',
            '/static/departments/hr/policies.html': '/app/policies',
            '/static/departments/development/projects.html': '/app/projects',
            
            // Profile pages
            '/static/profile.html': '/app/profile',
            '/static/profile-details.html': '/app/profile/details',
            '/static/profile-documents.html': '/app/profile/documents',
            '/static/salary.html': '/app/salary',
            '/static/salary-slips.html': '/app/salary/slips',
            '/static/penalties.html': '/app/penalties'
        };

        return urlMappings[oldPath] || oldPath;
    }

    /**
     * Navigate to a clean URL
     * @param {string} path - Path to navigate to (can be old or new format)
     * @param {boolean} newTab - Open in new tab
     */
    navigateTo(path, newTab = false) {
        const cleanUrl = this.convertToCleanUrl(path);
        
        if (newTab) {
            window.open(cleanUrl, '_blank');
        } else {
            window.location.href = cleanUrl;
        }
    }

    /**
     * Update all navigation links on a page to use clean URLs
     */
    updatePageNavigation() {
        // Update all anchor tags
        const links = document.querySelectorAll('a[href]');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('/static/')) {
                const cleanUrl = this.convertToCleanUrl(href);
                link.setAttribute('href', cleanUrl);
            }
        });

        // Update form actions
        const forms = document.querySelectorAll('form[action]');
        forms.forEach(form => {
            const action = form.getAttribute('action');
            if (action && action.startsWith('/static/')) {
                const cleanUrl = this.convertToCleanUrl(action);
                form.setAttribute('action', cleanUrl);
            }
        });

        // Update JavaScript redirects
        const scripts = document.querySelectorAll('script');
        scripts.forEach(script => {
            if (script.textContent && script.textContent.includes('/static/')) {
                // This is a simple text replacement - more sophisticated parsing might be needed
                let content = script.textContent;
                Object.keys(this.convertToCleanUrl).forEach(oldPath => {
                    content = content.replace(new RegExp(oldPath, 'g'), this.convertToCleanUrl(oldPath));
                });
                script.textContent = content;
            }
        });
    }

    /**
     * Get breadcrumb for current page
     * @param {string} currentPath - Current page path
     * @param {Object} user - User object with role and department
     * @returns {Array} - Breadcrumb items
     */
    getBreadcrumb(currentPath, user = null) {
        const breadcrumbs = [];
        
        // Add home/dashboard
        if (user) {
            const dashboardUrl = NavigationConfig.getDashboardUrl(user.role, user.department);
            breadcrumbs.push({ text: 'Dashboard', url: dashboardUrl });
        } else {
            breadcrumbs.push({ text: 'Dashboard', url: '/app/dashboard' });
        }

        // Parse current path
        const pathParts = currentPath.split('/').filter(part => part);
        
        if (pathParts.length > 1) {
            // Add department if applicable
            if (pathParts[1] === 'dashboard' && pathParts[2]) {
                const department = pathParts[2];
                breadcrumbs.push({ 
                    text: department.charAt(0).toUpperCase() + department.slice(1), 
                    url: `/app/dashboard/${department}` 
                });
            }
            
            // Add page specific breadcrumbs
            switch (pathParts[pathParts.length - 1]) {
                case 'customers':
                    breadcrumbs.push({ text: 'Customers', url: '/app/customers' });
                    break;
                case 'leads':
                    breadcrumbs.push({ text: 'Leads', url: '/app/leads' });
                    break;
                case 'employees':
                    breadcrumbs.push({ text: 'Employees', url: '/app/employees' });
                    break;
                case 'recruitment':
                    breadcrumbs.push({ text: 'Recruitment', url: '/app/recruitment' });
                    break;
                case 'projects':
                    breadcrumbs.push({ text: 'Projects', url: '/app/projects' });
                    break;
                case 'settings':
                    breadcrumbs.push({ text: 'Settings', url: '/app/settings' });
                    break;
                case 'profile':
                    breadcrumbs.push({ text: 'Profile', url: '/app/profile' });
                    break;
            }
        }

        return breadcrumbs;
    }

    /**
     * Initialize navigation system on page load
     */
    init() {
        // Update all navigation on page load
        this.updatePageNavigation();

        // Set up dynamic navigation updates
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Update navigation for newly added elements
                            const links = node.querySelectorAll ? node.querySelectorAll('a[href]') : [];
                            links.forEach(link => {
                                const href = link.getAttribute('href');
                                if (href && href.startsWith('/static/')) {
                                    const cleanUrl = this.convertToCleanUrl(href);
                                    link.setAttribute('href', cleanUrl);
                                }
                            });
                        }
                    });
                }
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }
}

// Create global instance
const navigationUtils = new NavigationUtils();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => navigationUtils.init());
} else {
    navigationUtils.init();
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NavigationUtils, navigationUtils };
}

// Make available globally
window.NavigationUtils = NavigationUtils;
window.navigationUtils = navigationUtils;
