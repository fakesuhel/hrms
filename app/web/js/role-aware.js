/**
 * Role-Aware API Utility Module
 * Current Date: 2025-06-11 09:48:00
 * User: soheru
 */

/**
 * Handles API requests with proper role checks and error handling
 */
const RoleAwareAPI = {
    // Store user's role once fetched
    userRole: null,
    
    /**
     * Check if current user has team management permissions
     */
    async hasTeamAccess() {
        if (this.userRole) {
            return ['team_lead', 'manager', 'admin'].includes(this.userRole);
        }
        
        try {
            // Get current user if needed
            const user = await this.getCurrentUser();
            return ['team_lead', 'manager', 'admin'].includes(user.role);
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