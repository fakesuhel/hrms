// universal-sidebar.js
// Enhanced sidebar management with proper active state handling
window.universalSidebar = {
    manualInit: function(user) {
        // Populate sidebar with user info
        this.updateUserInfo(user);
        // Set active navigation item based on current page
        this.setActiveNavItem();
    },
    
    updateUserInfo: function(user) {
        // Update sidebar user information
        const usernameEl = document.getElementById('sidebar-username');
        if (usernameEl) {
            usernameEl.textContent = user.full_name || user.username || 'Unknown User';
        }
        
        const positionEl = document.getElementById('sidebar-position');
        if (positionEl) {
            positionEl.textContent = user.position || user.role || 'Employee';
        }
    },
    
    setActiveNavItem: function() {
        // Get current page path
        const currentPath = window.location.pathname;
        
        // Remove active class from all nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Determine which nav item should be active based on current path
        let activeSelector = null;
        
        if (currentPath.includes('/dashboard')) {
            activeSelector = 'a[href*="/dashboard"]';
        } else if (currentPath.includes('/attendance')) {
            activeSelector = 'a[href*="/attendance"]';
        } else if (currentPath.includes('/leads')) {
            activeSelector = 'a[href*="/leads"]';
        } else if (currentPath.includes('/customers')) {
            activeSelector = 'a[href*="/customers"]';
        } else if (currentPath.includes('/reports')) {
            activeSelector = 'a[href*="/reports"]';
        } else if (currentPath.includes('/profile')) {
            activeSelector = 'a[href*="/profile"]';
        }
        
        // Set active class on the correct nav item
        if (activeSelector) {
            const activeLink = document.querySelector(activeSelector);
            if (activeLink) {
                activeLink.classList.add('active');
            }
        }
    },
    
    // Function to ensure sidebar consistency across all pages
    ensureSidebarConsistency: function() {
        // Check if sidebar needs updates
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;
        
        // Ensure proper icon spacing
        const navLinks = sidebar.querySelectorAll('.nav-link i');
        navLinks.forEach(icon => {
            icon.style.width = '24px';
            icon.style.height = '24px';
            icon.style.display = 'flex';
            icon.style.alignItems = 'center';
            icon.style.justifyContent = 'center';
            icon.style.marginRight = '0.75rem';
            icon.style.fontSize = '1.1rem';
        });
        
        // Ensure consistent navigation structure
        this.setActiveNavItem();
    }
};

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar consistency
    if (window.universalSidebar) {
        window.universalSidebar.ensureSidebarConsistency();
    }
    
    // Re-check active state after a brief delay to ensure page is fully loaded
    setTimeout(() => {
        if (window.universalSidebar) {
            window.universalSidebar.setActiveNavItem();
        }
    }, 100);
});

// Handle navigation clicks to update active state
document.addEventListener('click', function(event) {
    if (event.target.closest('.nav-link')) {
        // Small delay to allow navigation to complete
        setTimeout(() => {
            if (window.universalSidebar) {
                window.universalSidebar.setActiveNavItem();
            }
        }, 50);
    }
});
