/**
 * Role-Based Access Control System
 * Enhanced for comprehensive department and role management
 * Current Date: 2025-07-19
 */

// Department and Role Definitions
const DEPARTMENTS = {
    MANAGEMENT: 'management',
    SALES: 'sales',
    DEVELOPMENT: 'development'
};

const ROLES = {
    // Management Department
    DIRECTOR: 'director',
    HR: 'hr',
    
    // Sales Department
    SALES_MANAGER: 'sales_manager',
    SALES_EXECUTIVE: 'sales_executive',
    
    // Development Department
    DEV_MANAGER: 'dev_manager',
    TEAM_LEAD: 'team_lead',
    DEVELOPER: 'developer',
    INTERN: 'intern'
};

// Navigation structure based on roles
const NAVIGATION_CONFIG = {
    [ROLES.DIRECTOR]: {
        department: DEPARTMENTS.MANAGEMENT,
        navigation: [
            { href: '/dashboard.html', icon: '🏠', text: 'Dashboard', access: 'all' },
            { href: '/attendance.html', icon: '⏰', text: 'Attendance', access: 'all' },
            { href: '/users.html', icon: '👥', text: 'All Employees', access: 'manage' },
            { href: '/daily-reports.html', icon: '📋', text: 'Daily Reports', access: 'all' },
            { href: '/projects.html', icon: '📂', text: 'Projects', access: 'all' },
            { href: '/leads.html', icon: '🎯', text: 'Leads', access: 'all' },
            { href: '/leave-requests.html', icon: '🏖️', text: 'Leave Requests', access: 'all' },
            { href: '/performance-reviews.html', icon: '⭐', text: 'Performance', access: 'all' },
            { href: '/penalties.html', icon: '⚠️', text: 'Penalties', access: 'all' },
            { href: '/salary.html', icon: '💰', text: 'Salary Management', access: 'all' },
            { href: '/profile.html', icon: '👤', text: 'Profile', access: 'own' }
        ]
    },
    
    [ROLES.HR]: {
        department: DEPARTMENTS.MANAGEMENT,
        navigation: [
            { href: '/dashboard.html', icon: '🏠', text: 'Dashboard', access: 'limited' },
            { href: '/attendance.html', icon: '⏰', text: 'Attendance', access: 'manage' },
            { href: '/users.html', icon: '👥', text: 'All Employees', access: 'manage' },
            { href: '/daily-reports.html', icon: '📋', text: 'Daily Reports', access: 'view_all' },
            { href: '/leave-requests.html', icon: '🏖️', text: 'Leave Requests', access: 'approve' },
            { href: '/performance-reviews.html', icon: '⭐', text: 'Performance', access: 'view_all' },
            { href: '/salary.html', icon: '💰', text: 'Salary Management', access: 'generate' },
            { href: '/profile.html', icon: '👤', text: 'Profile', access: 'own' }
        ]
    },
    
    [ROLES.SALES_MANAGER]: {
        department: DEPARTMENTS.SALES,
        navigation: [
            { href: '/dashboard.html', icon: '🏠', text: 'Dashboard', access: 'sales_team' },
            { href: '/attendance.html', icon: '⏰', text: 'Attendance', access: 'team' },
            { href: '/leads.html', icon: '🎯', text: 'Leads', access: 'team_manage' },
            { href: '/daily-reports.html', icon: '📋', text: 'Daily Reports', access: 'team' },
            { href: '/payments.html', icon: '💳', text: 'Payment Tracking', access: 'team' },
            { href: '/profile.html', icon: '👤', text: 'Profile', access: 'own' }
        ]
    },
    
    [ROLES.SALES_EXECUTIVE]: {
        department: DEPARTMENTS.SALES,
        navigation: [
            { href: '/dashboard.html', icon: '🏠', text: 'Dashboard', access: 'sales' },
            { href: '/attendance.html', icon: '⏰', text: 'Attendance', access: 'own' },
            { href: '/leads.html', icon: '🎯', text: 'Leads', access: 'own' },
            { href: '/daily-reports.html', icon: '📋', text: 'Daily Reports', access: 'own' },
            { href: '/payments.html', icon: '💳', text: 'Payment Tracking', access: 'own' },
            { href: '/profile.html', icon: '👤', text: 'Profile', access: 'own' }
        ]
    },
    
    [ROLES.DEV_MANAGER]: {
        department: DEPARTMENTS.DEVELOPMENT,
        navigation: [
            { href: '/dashboard.html', icon: '🏠', text: 'Dashboard', access: 'dev_all' },
            { href: '/attendance.html', icon: '⏰', text: 'Attendance', access: 'team' },
            { href: '/projects.html', icon: '📂', text: 'Projects', access: 'all_dev' },
            { href: '/daily-reports.html', icon: '📋', text: 'Daily Reports', access: 'team' },
            { href: '/performance-reviews.html', icon: '⭐', text: 'Performance', access: 'team' },
            { href: '/leave-requests.html', icon: '🏖️', text: 'Leave Requests', access: 'own' },
            { href: '/penalties.html', icon: '⚠️', text: 'Penalties', access: 'team' },
            { href: '/profile.html', icon: '👤', text: 'Profile', access: 'own' }
        ]
    },
    
    [ROLES.TEAM_LEAD]: {
        department: DEPARTMENTS.DEVELOPMENT,
        navigation: [
            { href: '/dashboard.html', icon: '🏠', text: 'Dashboard', access: 'employee' },
            { href: '/attendance.html', icon: '⏰', text: 'Attendance', access: 'team_view' },
            { href: '/projects.html', icon: '📂', text: 'Projects', access: 'assigned_create' },
            { href: '/daily-reports.html', icon: '📋', text: 'Daily Reports', access: 'team_view' },
            { href: '/performance-reviews.html', icon: '⭐', text: 'Performance', access: 'own' },
            { href: '/leave-requests.html', icon: '🏖️', text: 'Leave Requests', access: 'own' },
            { href: '/penalties.html', icon: '⚠️', text: 'Penalties', access: 'team_warn' },
            { href: '/profile.html', icon: '👤', text: 'Profile', access: 'team_view' }
        ]
    },
    
    [ROLES.DEVELOPER]: {
        department: DEPARTMENTS.DEVELOPMENT,
        navigation: [
            { href: '/dashboard.html', icon: '🏠', text: 'Dashboard', access: 'employee' },
            { href: '/attendance.html', icon: '⏰', text: 'Attendance', access: 'own' },
            { href: '/projects.html', icon: '📂', text: 'Projects', access: 'assigned_only' },
            { href: '/daily-reports.html', icon: '📋', text: 'Daily Reports', access: 'own' },
            { href: '/performance-reviews.html', icon: '⭐', text: 'Performance', access: 'own' },
            { href: '/leave-requests.html', icon: '🏖️', text: 'Leave Requests', access: 'own' },
            { href: '/penalties.html', icon: '⚠️', text: 'Penalties', access: 'own' },
            { href: '/profile.html', icon: '👤', text: 'Profile', access: 'own' }
        ]
    },
    
    [ROLES.INTERN]: {
        department: DEPARTMENTS.DEVELOPMENT,
        navigation: [
            { href: '/dashboard.html', icon: '🏠', text: 'Dashboard', access: 'employee' },
            { href: '/attendance.html', icon: '⏰', text: 'Attendance', access: 'own' },
            { href: '/projects.html', icon: '📂', text: 'Projects', access: 'assigned_only' },
            { href: '/daily-reports.html', icon: '📋', text: 'Daily Reports', access: 'own' },
            { href: '/performance-reviews.html', icon: '⭐', text: 'Performance', access: 'own' },
            { href: '/leave-requests.html', icon: '🏖️', text: 'Leave Requests', access: 'own' },
            { href: '/penalties.html', icon: '⚠️', text: 'Penalties', access: 'own' },
            { href: '/profile.html', icon: '👤', text: 'Profile', access: 'own' }
        ]
    }
};

// Legacy role mapping for backward compatibility
const LEGACY_ROLE_MAPPING = {
    'director': ROLES.DIRECTOR,
    'hr': ROLES.HR,
    'manager': ROLES.DEV_MANAGER,
    'team_lead': ROLES.TEAM_LEAD,
    'employee': ROLES.DEVELOPER,
    'admin': ROLES.DIRECTOR
};

// Get user's role (with legacy support)
function getUserRole(user) {
    if (!user || !user.role) return ROLES.DEVELOPER; // Default role
    
    // Check if it's a new role format
    if (Object.values(ROLES).includes(user.role)) {
        return user.role;
    }
    
    // Map legacy roles
    return LEGACY_ROLE_MAPPING[user.role] || ROLES.DEVELOPER;
}

// Get navigation items for a specific role
function getNavigationForRole(userRole) {
    return NAVIGATION_CONFIG[userRole] || NAVIGATION_CONFIG[ROLES.DEVELOPER];
}

// Get display name for role
function getRoleDisplayName(role) {
    const roleNames = {
        [ROLES.DIRECTOR]: 'Director',
        [ROLES.HR]: 'HR',
        [ROLES.SALES_MANAGER]: 'Sales Manager',
        [ROLES.SALES_EXECUTIVE]: 'Sales Executive',
        [ROLES.DEV_MANAGER]: 'Development Manager',
        [ROLES.TEAM_LEAD]: 'Team Lead',
        [ROLES.DEVELOPER]: 'Developer',
        [ROLES.INTERN]: 'Intern'
    };
    return roleNames[role] || 'Employee';
}

// Check if user has access to a specific feature
function hasAccess(user, feature, targetUserId = null) {
    const userRole = getUserRole(user);
    const currentUserId = user.id || user._id;
    
    switch (userRole) {
        case ROLES.DIRECTOR:
            return true; // Director has access to everything
            
        case ROLES.HR:
            return ['attendance_manage', 'users_manage', 'salary_generate', 'leave_approve', 'profile_view'].includes(feature);
            
        case ROLES.SALES_MANAGER:
            if (feature === 'team_data' && targetUserId && user.team_members && user.team_members.includes(targetUserId)) {
                return true;
            }
            return ['leads_team', 'attendance_team', 'reports_team'].includes(feature);
            
        case ROLES.SALES_EXECUTIVE:
            return ['leads_own', 'dashboard_sales'].includes(feature) || 
                   (feature === 'profile_view' && (targetUserId === currentUserId || !targetUserId));
            
        case ROLES.DEV_MANAGER:
            return ['projects_all', 'attendance_team', 'reports_team', 'penalties_team'].includes(feature);
            
        case ROLES.TEAM_LEAD:
            if (feature === 'team_data' && targetUserId && user.team_members && user.team_members.includes(targetUserId)) {
                return true;
            }
            return ['projects_create', 'penalties_warn', 'profile_team'].includes(feature);
            
        case ROLES.DEVELOPER:
        case ROLES.INTERN:
            return ['projects_assigned', 'profile_own'].includes(feature) || 
                   (feature === 'profile_view' && (targetUserId === currentUserId || !targetUserId));
            
        default:
            return false;
    }
}

// Generate navigation HTML (preserving existing sidebar structure)
function generateNavigationItems(user, currentPage = '') {
    const userRole = getUserRole(user);
    const config = getNavigationForRole(userRole);
    const currentPath = currentPage || window.location.pathname.split('/').pop() || 'dashboard.html';
    
    return config.navigation.map(item => `
        <li class="nav-item">
            <a href="${item.href}" class="nav-link ${currentPath === item.href.split('/').pop() ? 'active' : ''}">
                <span style="margin-right: 0.75rem;">${item.icon}</span>
                ${item.text}
            </a>
        </li>
    `).join('');
}

// Update existing sidebar with role-based navigation (preserving UI)
function updateSidebarNavigation(user, currentPage = '') {
    const navList = document.querySelector('.nav-list');
    if (navList) {
        navList.innerHTML = generateNavigationItems(user, currentPage);
    }
    
    // Update user info if exists
    const userFullname = document.querySelector('.user-fullname');
    const userRole = document.querySelector('.user-role');
    
    if (userFullname) {
        userFullname.textContent = user.full_name || user.username || 'User';
    }
    
    if (userRole) {
        userRole.textContent = getRoleDisplayName(getUserRole(user));
    }
}

// Enhanced Role-Aware API with comprehensive role support
const RoleAwareAPI = {
    // Store user's role once fetched
    userRole: null,

    /**
     * Check if current user has team management permissions
     */
    async hasTeamAccess() {
        if (this.userRole) {
            return ['team_lead', 'manager', 'admin', 'director', 'hr', 'sales_manager', 'dev_manager'].includes(this.userRole);
        }

        try {
            // Get current user if needed
            const user = await this.getCurrentUser();
            const role = getUserRole(user);
            return hasAccess(user, 'team_data');
        } catch (error) {
            console.error('Error checking team access:', error);
            return false;
        }
    },

    /**
     * Get current user and store role
     */
    async getCurrentUser() {
        try {
            const token = localStorage.getItem('bhoomitechzone_token');

            if (!token) {
                throw new Error('Not authenticated');
            }

            const response = await fetch('/users/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to get user data');
            }

            const userData = await response.json();
            this.userRole = userData.role;
            return userData;
        } catch (error) {
            console.error('Error getting user data:', error);
            throw error;
        }
    },

    /**
     * Get role-based dashboard statistics
     */
    async getDashboardStats() {
        try {
            // Check user role to determine which dashboard data to fetch
            const hasTeamAccess = await this.hasTeamAccess();

            // Token for API authorization
            const token = localStorage.getItem('bhoomitechzone_token');

            let endpoint = hasTeamAccess ? '/dashboard/team-stats' : '/dashboard/employee-stats';

            const response = await fetch(endpoint, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch dashboard data');
            }

            const dashboardData = await response.json();

            // Add a flag indicating if this is team view data
            dashboardData.isTeamView = hasTeamAccess;

            return dashboardData;
        } catch (error) {
            console.error('Error fetching dashboard statistics:', error);

            // Return a default structure with isTeamView flag
            // This ensures the UI can still render even if the API call fails
            return {
                isTeamView: false,
                attendance: { personal_rate: 0 },
                projects: { assigned_count: 0 },
                performance: { personal_rating: 'N/A' },
                leave: { available_days: 0 },
                error: error.message
            };
        }
    },

    /**
     * Safely retrieve team attendance data
     */
    async getTeamAttendance(date) {
        if (!await this.hasTeamAccess()) {
            return { error: 'Not authorized', status: 403 };
        }

        try {
            const token = localStorage.getItem('bhoomitechzone_token');
            const dateStr = date.toISOString().split('T')[0];
            const response = await fetch(`/attendance/team?for_date=${dateStr}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 403) {
                return { error: 'Permission denied', status: 403 };
            }

            if (!response.ok) {
                return { error: 'Request failed', status: response.status };
            }

            return { data: await response.json() };
        } catch (error) {
            console.error('Error fetching team attendance:', error);
            return { error: error.message };
        }
    },

    /**
     * Safely retrieve pending leave requests
     */
    async getPendingLeaveRequests() {
        if (!await this.hasTeamAccess()) {
            return { error: 'Not authorized', status: 403 };
        }

        try {
            const token = localStorage.getItem('bhoomitechzone_token');
            const response = await fetch('/leave-requests/pending-approval', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 403) {
                return { error: 'Permission denied', status: 403 };
            }

            if (!response.ok) {
                return { error: 'Request failed', status: response.status };
            }

            return { data: await response.json() };
        } catch (error) {
            console.error('Error fetching pending leave requests:', error);
            return { error: error.message };
        }
    },

    /**
     * Safely retrieve team daily reports
     */
    async getTeamReports() {
        if (!await this.hasTeamAccess()) {
            return { error: 'Not authorized', status: 403 };
        }

        try {
            const token = localStorage.getItem('bhoomitechzone_token');
            const response = await fetch('/daily-reports/team/today', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 403) {
                return { error: 'Permission denied', status: 403 };
            }

            if (!response.ok) {
                return { error: 'Request failed', status: response.status };
            }

            return { data: await response.json() };
        } catch (error) {
            console.error('Error fetching team reports:', error);
            return { error: error.message };
        }
    },

    /**
     * Get personal leave balance as fallback when not authorized for team view
     */
    async getPersonalLeaveBalance() {
        try {
            const token = localStorage.getItem('bhoomitechzone_token');
            const response = await fetch('/leave-requests/balance', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                return { error: 'Request failed', status: response.status };
            }

            return { data: await response.json() };
        } catch (error) {
            console.error('Error fetching leave balance:', error);
            return { error: error.message };
        }
    },

    /**
     * Get personal attendance stats as fallback when not authorized for team view 
     */
    async getPersonalAttendanceStats() {
        try {
            const token = localStorage.getItem('bhoomitechzone_token');
            const today = new Date();
            const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

            const start = firstDayOfMonth.toISOString().split('T')[0];
            const end = today.toISOString().split('T')[0];

            const response = await fetch(`/attendance/stats?start_date=${start}&end_date=${end}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                return { error: 'Request failed', status: response.status };
            }

            return { data: await response.json() };
        } catch (error) {
            console.error('Error fetching attendance stats:', error);
            return { error: error.message };
        }
    }
};

// Export functions for global use
window.RoleManager = {
    ROLES,
    DEPARTMENTS,
    getUserRole,
    getNavigationForRole,
    getRoleDisplayName,
    hasAccess,
    generateNavigationItems,
    updateSidebarNavigation,
    RoleAwareAPI
};

// Update sidebar time display
function updateSidebarTime() {
    const timeElement = document.getElementById('sidebarTime');
    if (timeElement) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { 
            hour12: true, 
            hour: 'numeric', 
            minute: '2-digit',
            second: '2-digit'
        });
        timeElement.textContent = timeString;
    }
}

// Auto-update sidebar time
setInterval(updateSidebarTime, 1000);