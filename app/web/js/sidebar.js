/**
 * Sidebar Component Module
 * Handles sidebar initialization, navigation, and user data loading
 */

class SidebarComponent {
    constructor() {
        this.currentPage = this.getCurrentPageFromURL();
        this.userData = null;
    }

    /**
     * Initialize the sidebar component
     */
    async init() {
        await this.loadSidebarHTML();
        await this.loadUserData();
        this.setActiveNavItem();
        this.setupEventListeners();
    }

    /**
     * Load sidebar HTML from component file
     */
    async loadSidebarHTML() {
        try {
            const response = await fetch('/static/components/sidebar.html');
            if (!response.ok) {
                throw new Error('Failed to load sidebar component');
            }
            const sidebarHTML = await response.text();
            
            // Find the sidebar container or create one
            let sidebarContainer = document.querySelector('.sidebar');
            if (!sidebarContainer) {
                // Create sidebar container if it doesn't exist
                const dashboardContainer = document.querySelector('.dashboard-container');
                if (dashboardContainer) {
                    sidebarContainer = document.createElement('div');
                    dashboardContainer.insertBefore(sidebarContainer, dashboardContainer.firstChild);
                }
            }
            
            if (sidebarContainer) {
                sidebarContainer.outerHTML = sidebarHTML;
            } else {
                console.error('Could not find dashboard container to insert sidebar');
            }
        } catch (error) {
            console.error('Error loading sidebar:', error);
        }
    }

    /**
     * Load user data and update sidebar
     */
    async loadUserData() {
        try {
            const token = localStorage.getItem('bhoomitechzone_token');
            if (!token) {
                window.location.href = '/static/login.html';
                return;
            }

            const response = await fetch('/users/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('bhoomitechzone_token');
                    window.location.href = '/static/login.html';
                    return;
                }
                throw new Error('Failed to fetch user data');
            }

            this.userData = await response.json();
            this.updateSidebarUserInfo();
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    /**
     * Update sidebar with user information
     */
    updateSidebarUserInfo() {
        if (!this.userData) return;

        const usernameElement = document.getElementById('sidebar-username');
        const positionElement = document.getElementById('sidebar-position');

        if (usernameElement) {
            usernameElement.textContent = this.userData.full_name || this.userData.username || 'Unknown User';
        }

        if (positionElement) {
            positionElement.textContent = this.userData.position || this.userData.role || 'Employee';
        }
    }

    /**
     * Get current page from URL
     */
    getCurrentPageFromURL() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();
        
        // Map filenames to page identifiers
        const pageMap = {
            'dashboard.html': 'dashboard',
            'attendance.html': 'attendance',
            'projects.html': 'projects',
            'daily-reports.html': 'daily-reports',
            'teams.html': 'teams',
            'performance-reviews.html': 'performance-reviews',
            'leave-requests.html': 'leave-requests',
            'settings.html': 'settings'
        };

        return pageMap[filename] || 'dashboard';
    }

    /**
     * Set active navigation item based on current page
     */
    setActiveNavItem() {
        // Remove active class from all nav links
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => link.classList.remove('active'));

        // Add active class to current page link
        const currentNavLink = document.querySelector(`[data-page="${this.currentPage}"]`);
        if (currentNavLink) {
            currentNavLink.classList.add('active');
        }
    }

    /**
     * Setup event listeners for sidebar interactions
     */
    setupEventListeners() {
        // Menu toggle functionality
        const menuToggle = document.getElementById('menuToggle');
        const dashboardContainer = document.querySelector('.dashboard-container');
        
        if (menuToggle && dashboardContainer) {
            menuToggle.addEventListener('click', () => {
                dashboardContainer.classList.toggle('sidebar-hidden');
            });
        }

        // Navigation link click handlers
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                // Update active state immediately for better UX
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });

        // Close sidebar on mobile when clicking outside
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                const sidebar = document.querySelector('.sidebar');
                const menuToggle = document.getElementById('menuToggle');
                
                if (sidebar && !sidebar.contains(e.target) && e.target !== menuToggle) {
                    const dashboardContainer = document.querySelector('.dashboard-container');
                    if (dashboardContainer) {
                        dashboardContainer.classList.add('sidebar-hidden');
                    }
                }
            }
        });
    }

    /**
     * Get user data
     */
    getUserData() {
        return this.userData;
    }

    /**
     * Update user info in sidebar
     */
    updateUserInfo(userData) {
        this.userData = userData;
        this.updateSidebarUserInfo();
    }
}

// Global sidebar instance
window.sidebarComponent = new SidebarComponent();

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    await window.sidebarComponent.init();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SidebarComponent;
}
