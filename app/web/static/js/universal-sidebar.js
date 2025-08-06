// universal-sidebar.js
// Minimal stub to prevent 404 and allow sidebar initialization
window.universalSidebar = {
    manualInit: function(user) {
        // Example: populate sidebar with user info
        const sidebar = document.querySelector('.sidebar');
        if (sidebar && user) {
            sidebar.innerHTML = `
                <div class="sidebar-user">
                    <div class="sidebar-avatar">${user.full_name ? user.full_name[0] : 'U'}</div>
                    <div class="sidebar-username">${user.full_name || user.username || 'User'}</div>
                    <div class="sidebar-role">${user.position || user.role || ''}</div>
                </div>
                <ul class="sidebar-menu">
                    <li><a href="/app/sales/profile">Profile</a></li>
                    <li><a href="/app/sales/attendance">Attendance</a></li>
                    <li><a href="/app/sales/payroll">Payroll</a></li>
                    <li><a href="/app/sales/leaves">Leaves</a></li>
                </ul>
            `;
        }
    }
};
