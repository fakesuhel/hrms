// Role-Based Access Control System
// This script maintains the exact same UI while controlling access based on user roles

class RoleManager {
    constructor() {
        this.roleHierarchy = {
            // Management Department
            'director': {
                department: 'management',
                level: 10,
                permissions: ['all_access']
            },
            'hr': {
                department: 'management', 
                level: 8,
                permissions: [
                    'attendance_check', 'attendance_modify', 'mark_absent', 'mark_present',
                    'employee_profiles_view', 'employee_profiles_edit', 'employee_documents_view',
                    'employee_add', 'employee_status_control',
                    'salary_slips_generate', 'salary_processing_check', 'incentives_add',
                    'daily_reports_all', 'leave_requests_approve'
                ]
            },
            
            // Sales Department
            'sales_manager': {
                department: 'sales',
                level: 7,
                permissions: [
                    'team_attendance_view', 'self_attendance',
                    'leads_view_all', 'leads_edit_all', 'leads_create',
                    'reports_consolidated', 'payment_milestones',
                    'team_dashboard'
                ]
            },
            'sales_executive': {
                department: 'sales', 
                level: 5,
                permissions: [
                    'self_attendance', 'self_profile',
                    'leads_create', 'leads_own_view', 'leads_own_edit',
                    'payment_milestones_own', 'dashboard_sales'
                ]
            },
            
            // Development Department
            'dev_manager': {
                department: 'development',
                level: 7,
                permissions: [
                    'team_attendance_view', 'self_attendance',
                    'projects_all_view', 'projects_create', 'projects_start',
                    'daily_reports_all', 'performance_all_view',
                    'team_profiles_view', 'penalties_team_assign',
                    'dashboard_consolidated'
                ]
            },
            'team_lead': {
                department: 'development',
                level: 6,
                permissions: [
                    'team_attendance_view', 'self_attendance',
                    'projects_assigned_view', 'projects_create',
                    'daily_reports_team', 'performance_own_view',
                    'team_profiles_view', 'penalties_team_warn',
                    'leave_requests_own'
                ]
            },
            'developer': {
                department: 'development',
                level: 4,
                permissions: [
                    'self_attendance', 'self_profile',
                    'projects_assigned_view', 'daily_reports_own',
                    'performance_own_view', 'leave_requests_own',
                    'penalties_own_view'
                ]
            },
            'intern': {
                department: 'development',
                level: 2,
                permissions: [
                    'self_attendance', 'self_profile',
                    'projects_assigned_view', 'daily_reports_own',
                    'performance_own_view', 'leave_requests_own',
                    'penalties_own_view'
                ]
            },
            
            // Default fallback
            'employee': {
                department: 'general',
                level: 3,
                permissions: [
                    'self_attendance', 'self_profile',
                    'daily_reports_own', 'performance_own_view',
                    'leave_requests_own'
                ]
            }
        };

        this.navigationConfig = {
            director: [
                { icon: '📊', text: 'Dashboard', href: '/static/dashboard.html', id: 'dashboard' },
                { icon: '🕒', text: 'Attendance', href: '/static/attendance.html', id: 'attendance' },
                { icon: '📁', text: 'Projects', href: '/static/projects.html', id: 'projects' },
                { icon: '📝', text: 'Daily Reports', href: '/static/daily-reports.html', id: 'daily_reports' },
                { icon: '👥', text: 'Team', href: '/static/teams.html', id: 'team' },
                { icon: '💰', text: 'Sales Leads', href: '/departments/sales/leads.html', id: 'sales_leads' },
                { icon: '⭐', text: 'Performance', href: '/shared/performance-reviews.html', id: 'performance' },
                { icon: '📅', text: 'Leave Requests', href: '/shared/leave-requests.html', id: 'leave_requests' },
                { icon: '⚠️', text: 'Penalties', href: '/static/penalties.html', id: 'penalties' },
                { icon: '⚙️', text: 'Settings', href: '/static/settings.html', id: 'settings' }
            ],
            hr: [
                { icon: '📊', text: 'Dashboard', href: '/departments/hr/dashboard.html', id: 'dashboard' },
                { icon: '🕒', text: 'Attendance', href: '/static/attendance.html', id: 'attendance' },
                { icon: '👥', text: 'Employees', href: '/departments/hr/employees.html', id: 'employees' },
                { icon: '📝', text: 'Daily Reports', href: '/static/daily-reports.html', id: 'daily_reports' },
                { icon: '💰', text: 'Salary Management', href: '/departments/hr/salary.html', id: 'salary' },
                { icon: '📅', text: 'Leave Requests', href: '/shared/leave-requests.html', id: 'leave_requests' },
                { icon: '⭐', text: 'Performance', href: '/shared/performance-reviews.html', id: 'performance' },
                { icon: '⚠️', text: 'Penalties', href: '/static/penalties.html', id: 'penalties' }
            ],
            sales_manager: [
                { icon: '📊', text: 'Dashboard', href: '/departments/sales/dashboard.html', id: 'dashboard' },
                { icon: '🕒', text: 'Attendance', href: '/static/attendance.html', id: 'attendance' },
                { icon: '💰', text: 'Leads Management', href: '/departments/sales/leads.html', id: 'leads' },
                { icon: '👥', text: 'Team', href: '/static/teams.html', id: 'team' },
                { icon: '📝', text: 'Reports', href: '/departments/sales/reports.html', id: 'reports' },
                { icon: '🏢', text: 'Customers', href: '/departments/sales/customers.html', id: 'customers' },
                { icon: '⭐', text: 'Performance', href: '/shared/performance-reviews.html', id: 'performance' },
                { icon: '📅', text: 'Leave Requests', href: '/shared/leave-requests.html', id: 'leave_requests' }
            ],
            sales_executive: [
                { icon: '📊', text: 'Dashboard', href: '/departments/sales/dashboard.html', id: 'dashboard' },
                { icon: '🕒', text: 'Attendance', href: '/static/attendance.html', id: 'attendance' },
                { icon: '💰', text: 'My Leads', href: '/departments/sales/leads.html', id: 'leads' },
                { icon: '📝', text: 'Daily Reports', href: '/static/daily-reports.html', id: 'daily_reports' },
                { icon: '🏢', text: 'Customers', href: '/departments/sales/customers.html', id: 'customers' },
                { icon: '⭐', text: 'Performance', href: '/shared/performance-reviews.html', id: 'performance' },
                { icon: '📅', text: 'Leave Requests', href: '/shared/leave-requests.html', id: 'leave_requests' },
                { icon: '👤', text: 'Profile', href: '/static/profile.html', id: 'profile' }
            ],
            dev_manager: [
                { icon: '📊', text: 'Dashboard', href: '/departments/development/dashboard.html', id: 'dashboard' },
                { icon: '🕒', text: 'Attendance', href: '/static/attendance.html', id: 'attendance' },
                { icon: '📁', text: 'Projects', href: '/static/projects.html', id: 'projects' },
                { icon: '📝', text: 'Daily Reports', href: '/static/daily-reports.html', id: 'daily_reports' },
                { icon: '👥', text: 'Team', href: '/static/teams.html', id: 'team' },
                { icon: '⭐', text: 'Performance', href: '/shared/performance-reviews.html', id: 'performance' },
                { icon: '📅', text: 'Leave Requests', href: '/shared/leave-requests.html', id: 'leave_requests' },
                { icon: '⚠️', text: 'Penalties', href: '/static/penalties.html', id: 'penalties' }
            ],
            team_lead: [
                { icon: '📊', text: 'Dashboard', href: '/departments/development/dashboard.html', id: 'dashboard' },
                { icon: '🕒', text: 'Attendance', href: '/static/attendance.html', id: 'attendance' },
                { icon: '📁', text: 'Projects', href: '/static/projects.html', id: 'projects' },
                { icon: '📝', text: 'Daily Reports', href: '/static/daily-reports.html', id: 'daily_reports' },
                { icon: '👥', text: 'Team', href: '/static/teams.html', id: 'team' },
                { icon: '⭐', text: 'Performance', href: '/shared/performance-reviews.html', id: 'performance' },
                { icon: '📅', text: 'Leave Requests', href: '/shared/leave-requests.html', id: 'leave_requests' },
                { icon: '⚠️', text: 'Penalties', href: '/static/penalties.html', id: 'penalties' },
                { icon: '👤', text: 'Profile', href: '/static/profile.html', id: 'profile' }
            ],
            developer: [
                { icon: '📊', text: 'Dashboard', href: '/departments/development/dashboard.html', id: 'dashboard' },
                { icon: '🕒', text: 'Attendance', href: '/static/attendance.html', id: 'attendance' },
                { icon: '📁', text: 'Projects', href: '/static/projects.html', id: 'projects' },
                { icon: '📝', text: 'Daily Reports', href: '/static/daily-reports.html', id: 'daily_reports' },
                { icon: '⭐', text: 'Performance', href: '/shared/performance-reviews.html', id: 'performance' },
                { icon: '📅', text: 'Leave Requests', href: '/shared/leave-requests.html', id: 'leave_requests' },
                { icon: '⚠️', text: 'Penalties', href: '/static/penalties.html', id: 'penalties' },
                { icon: '👤', text: 'Profile', href: '/static/profile.html', id: 'profile' }
            ],
            intern: [
                { icon: '📊', text: 'Dashboard', href: '/departments/development/dashboard.html', id: 'dashboard' },
                { icon: '🕒', text: 'Attendance', href: '/static/attendance.html', id: 'attendance' },
                { icon: '📁', text: 'Projects', href: '/static/projects.html', id: 'projects' },
                { icon: '📝', text: 'Daily Reports', href: '/static/daily-reports.html', id: 'daily_reports' },
                { icon: '⭐', text: 'Performance', href: '/shared/performance-reviews.html', id: 'performance' },
                { icon: '📅', text: 'Leave Requests', href: '/shared/leave-requests.html', id: 'leave_requests' },
                { icon: '⚠️', text: 'Penalties', href: '/static/penalties.html', id: 'penalties' },
                { icon: '👤', text: 'Profile', href: '/static/profile.html', id: 'profile' }
            ]
        };
    }

    getCurrentUser() {
        try {
            const userStr = localStorage.getItem('bhoomitechzone_user');
            if (userStr) {
                return JSON.parse(userStr);
            }
            
            // Fallback to minimal user info
            return {
                username: localStorage.getItem('bhoomitechzone_username') || 'user',
                role: 'employee',
                department: 'general'
            };
        } catch (error) {
            console.error('Error getting user:', error);
            return { username: 'user', role: 'employee', department: 'general' };
        }
    }

    normalizeRole(role) {
        if (!role) return 'employee';
        
        const roleStr = role.toLowerCase().trim();
        const roleMapping = {
            'admin': 'director',
            'administrator': 'director',
            'hr_manager': 'hr',
            'human_resources': 'hr',
            'sales_lead': 'sales_manager',
            'sales_head': 'sales_manager',
            'sales_rep': 'sales_executive',
            'sales_representative': 'sales_executive',
            'development_manager': 'dev_manager',
            'dev_lead': 'team_lead',
            'team_leader': 'team_lead',
            'senior_developer': 'developer',
            'junior_developer': 'developer',
            'software_engineer': 'developer',
            'trainee': 'intern'
        };

        return roleMapping[roleStr] || roleStr || 'employee';
    }

    getUserRole(user) {
        const role = this.normalizeRole(user?.role);
        return this.roleHierarchy[role] ? role : 'employee';
    }

    hasPermission(user, permission) {
        const userRole = this.getUserRole(user);
        const roleConfig = this.roleHierarchy[userRole];
        
        // Director has all permissions
        if (userRole === 'director') return true;
        
        return roleConfig?.permissions?.includes(permission) || false;
    }

    canAccessPage(user, pageId) {
        const userRole = this.getUserRole(user);
        const navigation = this.navigationConfig[userRole] || this.navigationConfig.employee;
        
        return navigation.some(item => item.id === pageId);
    }

    generateSidebar(currentPage = '') {
        const user = this.getCurrentUser();
        const userRole = this.getUserRole(user);
        const navigation = this.navigationConfig[userRole] || this.navigationConfig.employee;
        
        // Get current page from URL if not provided
        if (!currentPage) {
            const path = window.location.pathname;
            currentPage = path.split('/').pop() || 'dashboard.html';
        }

        const navItems = navigation.map(item => {
            const isActive = currentPage.includes(item.href.split('/').pop()) || 
                           currentPage === item.id + '.html' ||
                           (item.href.includes(currentPage));
            
            return `
                <li class="nav-item">
                    <a href="${item.href}" class="nav-link ${isActive ? 'active' : ''}">
                        <i>${item.icon}</i>
                        ${item.text}
                    </a>
                </li>
            `;
        }).join('');

        return navItems;
    }

    updateSidebarNavigation() {
        const navList = document.querySelector('.nav-list');
        if (navList) {
            navList.innerHTML = this.generateSidebar();
        }
    }

    updateUserInfo() {
        const user = this.getCurrentUser();
        const userRole = this.getUserRole(user);
        const roleConfig = this.roleHierarchy[userRole];
        
        // Update sidebar user info
        const sidebarUsername = document.getElementById('sidebar-username');
        const sidebarPosition = document.getElementById('sidebar-position');
        
        if (sidebarUsername) {
            sidebarUsername.textContent = user.full_name || user.username || 'User';
        }
        
        if (sidebarPosition) {
            const roleDisplayNames = {
                'director': 'Director',
                'hr': 'HR Manager',
                'sales_manager': 'Sales Manager',
                'sales_executive': 'Sales Executive', 
                'dev_manager': 'Development Manager',
                'team_lead': 'Team Lead',
                'developer': 'Developer',
                'intern': 'Intern',
                'employee': 'Employee'
            };
            sidebarPosition.textContent = roleDisplayNames[userRole] || 'Employee';
        }

        // Update header user info
        const userInitials = document.getElementById('userInitials');
        const userFullName = document.getElementById('userFullName');
        
        if (userInitials) {
            const initials = (user.full_name || user.username || 'U').charAt(0).toUpperCase();
            userInitials.textContent = initials;
        }
        
        if (userFullName) {
            userFullName.textContent = user.full_name || user.username || 'User';
        }
    }

    // Content filtering based on role
    filterPageContent(pageType) {
        const user = this.getCurrentUser();
        const userRole = this.getUserRole(user);
        
        switch (pageType) {
            case 'attendance':
                this.filterAttendanceContent(user, userRole);
                break;
            case 'projects':
                this.filterProjectsContent(user, userRole);
                break;
            case 'daily_reports':
                this.filterDailyReportsContent(user, userRole);
                break;
            case 'team':
                this.filterTeamContent(user, userRole);
                break;
            case 'performance':
                this.filterPerformanceContent(user, userRole);
                break;
            case 'leave_requests':
                this.filterLeaveRequestsContent(user, userRole);
                break;
        }
    }

    filterAttendanceContent(user, userRole) {
        // Hide/show attendance management features based on role
        const adminFeatures = document.querySelectorAll('.admin-only, .hr-only, .manager-only');
        const canManageAttendance = this.hasPermission(user, 'attendance_modify');
        
        adminFeatures.forEach(element => {
            element.style.display = canManageAttendance ? 'block' : 'none';
        });
    }

    filterProjectsContent(user, userRole) {
        // Show only assigned projects for developers/interns
        if (['developer', 'intern'].includes(userRole)) {
            const createProjectBtn = document.querySelector('.create-project-btn');
            if (createProjectBtn) createProjectBtn.style.display = 'none';
        }
    }

    filterDailyReportsContent(user, userRole) {
        // HR and managers can see all reports, others only their own
        const allReportsView = document.querySelector('.all-reports-view');
        const canViewAllReports = this.hasPermission(user, 'daily_reports_all');
        
        if (allReportsView) {
            allReportsView.style.display = canViewAllReports ? 'block' : 'none';
        }
    }

    filterTeamContent(user, userRole) {
        // Only managers and above can see full team management
        const teamManagementFeatures = document.querySelectorAll('.team-management, .add-employee-btn');
        const canManageTeam = ['director', 'hr', 'sales_manager', 'dev_manager', 'team_lead'].includes(userRole);
        
        teamManagementFeatures.forEach(element => {
            element.style.display = canManageTeam ? 'block' : 'none';
        });
    }

    filterPerformanceContent(user, userRole) {
        // Limit performance reviews based on role
        const allPerformanceView = document.querySelector('.all-performance-view');
        const canViewAllPerformance = ['director', 'hr', 'sales_manager', 'dev_manager'].includes(userRole);
        
        if (allPerformanceView) {
            allPerformanceView.style.display = canViewAllPerformance ? 'block' : 'none';
        }
    }

    filterLeaveRequestsContent(user, userRole) {
        // Only HR and managers can approve leave requests
        const approveButtons = document.querySelectorAll('.approve-leave-btn, .reject-leave-btn');
        const canApproveLeave = this.hasPermission(user, 'leave_requests_approve');
        
        approveButtons.forEach(button => {
            button.style.display = canApproveLeave ? 'inline-block' : 'none';
        });
    }

    // Initialize the role system
    initialize() {
        this.updateSidebarNavigation();
        this.updateUserInfo();
        
        // Auto-detect page type and filter content
        const path = window.location.pathname;
        if (path.includes('attendance')) this.filterPageContent('attendance');
        else if (path.includes('projects')) this.filterPageContent('projects');
        else if (path.includes('daily-reports')) this.filterPageContent('daily_reports');
        else if (path.includes('team')) this.filterPageContent('team');
        else if (path.includes('performance')) this.filterPageContent('performance');
        else if (path.includes('leave-requests')) this.filterPageContent('leave_requests');
    }
}

// Global instance
window.roleManager = new RoleManager();

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.roleManager) {
        window.roleManager.initialize();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RoleManager;
}
