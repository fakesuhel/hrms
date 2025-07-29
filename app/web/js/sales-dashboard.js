/**
 * Sales Department Dashboard JavaScript
 * Integrates with Sales API endpoints for leads and customers management
 */

class SalesDashboard {
    constructor() {
        this.apiClient = window.hrmsApi;
        this.currentUser = null;
        this.leads = [];
        this.customers = [];
        this.leadStats = {};
        this.customerStats = {};
        
        this.init();
    }

    async init() {
        try {
            await this.loadCurrentUser();
            await this.loadDashboardData();
            this.setupEventListeners();
            this.renderDashboard();
        } catch (error) {
            console.error('Failed to initialize sales dashboard:', error);
            ApiHelpers.handleApiError(error);
        }
    }

    async loadCurrentUser() {
        // Get current user from role manager or API
        this.currentUser = window.currentUser || await this.apiClient.request('/users/me');
    }

    async loadDashboardData() {
        const loadingPromises = [
            this.loadLeads(),
            this.loadCustomers(),
            this.loadLeadStats(),
            this.loadCustomerStats()
        ];

        await Promise.all(loadingPromises);
    }

    async loadLeads() {
        try {
            this.leads = await this.apiClient.getLeads({ limit: 10 });
        } catch (error) {
            console.error('Failed to load leads:', error);
            this.leads = [];
        }
    }

    async loadCustomers() {
        try {
            this.customers = await this.apiClient.getCustomers({ limit: 10 });
        } catch (error) {
            console.error('Failed to load customers:', error);
            this.customers = [];
        }
    }

    async loadLeadStats() {
        try {
            this.leadStats = await this.apiClient.getLeadStats();
        } catch (error) {
            console.error('Failed to load lead stats:', error);
            this.leadStats = {};
        }
    }

    async loadCustomerStats() {
        try {
            this.customerStats = await this.apiClient.getCustomerStats();
        } catch (error) {
            console.error('Failed to load customer stats:', error);
            this.customerStats = {};
        }
    }

    renderDashboard() {
        this.renderStatsCards();
        this.renderRecentLeads();
        this.renderRecentCustomers();
        this.renderLeadsPipeline();
    }

    renderStatsCards() {
        const statsContainer = document.getElementById('sales-stats-cards');
        if (!statsContainer) return;

        const stats = [
            {
                title: 'Total Leads',
                value: this.leadStats.total_leads || 0,
                icon: '🎯',
                color: 'primary'
            },
            {
                title: 'Active Customers',
                value: this.customerStats.active || 0,
                icon: '👥',
                color: 'success'
            },
            {
                title: 'Pipeline Value',
                value: ApiHelpers.formatCurrency(this.leadStats.total_pipeline_value || 0),
                icon: '💰',
                color: 'info'
            },
            {
                title: 'Won Value',
                value: ApiHelpers.formatCurrency(this.leadStats.won_value || 0),
                icon: '🏆',
                color: 'warning'
            }
        ];

        statsContainer.innerHTML = stats.map(stat => `
            <div class="col-md-3 mb-3">
                <div class="card border-${stat.color}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-title text-muted">${stat.title}</h6>
                                <h4 class="text-${stat.color}">${stat.value}</h4>
                            </div>
                            <div class="text-${stat.color}" style="font-size: 2rem;">
                                ${stat.icon}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderRecentLeads() {
        const leadsContainer = document.getElementById('recent-leads');
        if (!leadsContainer) return;

        if (this.leads.length === 0) {
            leadsContainer.innerHTML = '<p class="text-muted">No leads found</p>';
            return;
        }

        leadsContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Contact</th>
                            <th>Status</th>
                            <th>Value</th>
                            <th>Priority</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.leads.slice(0, 5).map(lead => `
                            <tr>
                                <td>
                                    <strong>${lead.company_name}</strong><br>
                                    <small class="text-muted">${lead.business_type}</small>
                                </td>
                                <td>
                                    ${lead.contact_person}<br>
                                    <small class="text-muted">${lead.email}</small>
                                </td>
                                <td>
                                    <span class="badge bg-${this.getStatusColor(lead.status)}">
                                        ${lead.status}
                                    </span>
                                </td>
                                <td>
                                    ${lead.deal_value ? ApiHelpers.formatCurrency(lead.deal_value) : '-'}
                                </td>
                                <td>
                                    <span class="badge bg-${this.getPriorityColor(lead.priority)}">
                                        ${lead.priority}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="salesDashboard.viewLead('${lead.id}')">
                                        View
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderRecentCustomers() {
        const customersContainer = document.getElementById('recent-customers');
        if (!customersContainer) return;

        if (this.customers.length === 0) {
            customersContainer.innerHTML = '<p class="text-muted">No customers found</p>';
            return;
        }

        customersContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Contact</th>
                            <th>Status</th>
                            <th>Value</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.customers.slice(0, 5).map(customer => `
                            <tr>
                                <td>
                                    <strong>${customer.company_name}</strong><br>
                                    <small class="text-muted">${customer.business_type}</small>
                                </td>
                                <td>
                                    ${customer.contact_person}<br>
                                    <small class="text-muted">${customer.email}</small>
                                </td>
                                <td>
                                    <span class="badge bg-${this.getStatusColor(customer.status)}">
                                        ${customer.status}
                                    </span>
                                </td>
                                <td>
                                    ${ApiHelpers.formatCurrency(customer.customer_value || 0)}
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="salesDashboard.viewCustomer('${customer.id}')">
                                        View
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderLeadsPipeline() {
        const pipelineContainer = document.getElementById('leads-pipeline');
        if (!pipelineContainer) return;

        const stages = [
            { name: 'New', count: this.leadStats.new || 0, color: 'secondary' },
            { name: 'Contacted', count: this.leadStats.contacted || 0, color: 'primary' },
            { name: 'Qualified', count: this.leadStats.qualified || 0, color: 'info' },
            { name: 'Proposal', count: this.leadStats.proposal || 0, color: 'warning' },
            { name: 'Negotiation', count: this.leadStats.negotiation || 0, color: 'danger' },
            { name: 'Closed Won', count: this.leadStats.closed_won || 0, color: 'success' }
        ];

        pipelineContainer.innerHTML = `
            <div class="row">
                ${stages.map(stage => `
                    <div class="col-md-2 mb-3">
                        <div class="card border-${stage.color}">
                            <div class="card-body text-center">
                                <h6 class="card-title text-${stage.color}">${stage.name}</h6>
                                <h4>${stage.count}</h4>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    getStatusColor(status) {
        const colors = {
            'new': 'secondary',
            'contacted': 'primary',
            'qualified': 'info',
            'proposal': 'warning',
            'negotiation': 'danger',
            'closed_won': 'success',
            'closed_lost': 'dark',
            'active': 'success',
            'inactive': 'warning',
            'churned': 'danger'
        };
        return colors[status] || 'secondary';
    }

    getPriorityColor(priority) {
        const colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'urgent': 'dark'
        };
        return colors[priority] || 'secondary';
    }

    async viewLead(leadId) {
        try {
            const lead = await this.apiClient.getLeadById(leadId);
            this.showLeadModal(lead);
        } catch (error) {
            ApiHelpers.handleApiError(error);
        }
    }

    async viewCustomer(customerId) {
        try {
            const customer = await this.apiClient.getCustomerById(customerId);
            this.showCustomerModal(customer);
        } catch (error) {
            ApiHelpers.handleApiError(error);
        }
    }

    showLeadModal(lead) {
        // Create and show modal with lead details
        const modalHTML = `
            <div class="modal fade" id="leadModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Lead Details - ${lead.company_name}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Company Information</h6>
                                    <p><strong>Company:</strong> ${lead.company_name}</p>
                                    <p><strong>Contact Person:</strong> ${lead.contact_person}</p>
                                    <p><strong>Email:</strong> ${lead.email}</p>
                                    <p><strong>Phone:</strong> ${lead.phone}</p>
                                    <p><strong>Business Type:</strong> ${lead.business_type}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>Lead Details</h6>
                                    <p><strong>Status:</strong> <span class="badge bg-${this.getStatusColor(lead.status)}">${lead.status}</span></p>
                                    <p><strong>Priority:</strong> <span class="badge bg-${this.getPriorityColor(lead.priority)}">${lead.priority}</span></p>
                                    <p><strong>Source:</strong> ${lead.lead_source}</p>
                                    <p><strong>Budget Range:</strong> ${lead.budget_range}</p>
                                    <p><strong>Deal Value:</strong> ${lead.deal_value ? ApiHelpers.formatCurrency(lead.deal_value) : 'Not set'}</p>
                                    <p><strong>Lead Score:</strong> ${lead.lead_score}/100</p>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-12">
                                    <h6>Requirements</h6>
                                    <p>${lead.requirements}</p>
                                    ${lead.notes ? `<h6>Notes</h6><p>${lead.notes}</p>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" onclick="salesDashboard.editLead('${lead.id}')">Edit Lead</button>
                            <button type="button" class="btn btn-success" onclick="salesDashboard.convertToCustomer('${lead.id}')">Convert to Customer</button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal and add new one
        const existingModal = document.getElementById('leadModal');
        if (existingModal) existingModal.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('leadModal'));
        modal.show();
    }

    showCustomerModal(customer) {
        // Similar modal implementation for customer details
        console.log('Customer details:', customer);
        // Implementation similar to showLeadModal
    }

    setupEventListeners() {
        // Refresh dashboard data
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboardData().then(() => this.renderDashboard());
            });
        }

        // Search leads
        const searchInput = document.getElementById('search-leads');
        if (searchInput) {
            searchInput.addEventListener('input', ApiHelpers.debounce((e) => {
                this.searchLeads(e.target.value);
            }, 300));
        }

        // Filter by status
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterByStatus(e.target.value);
            });
        }
    }

    async searchLeads(query) {
        if (query.length < 2) {
            await this.loadLeads();
        } else {
            // Implement search functionality
            this.leads = this.leads.filter(lead => 
                lead.company_name.toLowerCase().includes(query.toLowerCase()) ||
                lead.contact_person.toLowerCase().includes(query.toLowerCase())
            );
        }
        this.renderRecentLeads();
    }

    async filterByStatus(status) {
        if (status === 'all') {
            await this.loadLeads();
        } else {
            this.leads = await this.apiClient.getLeads({ status });
        }
        this.renderRecentLeads();
    }

    async editLead(leadId) {
        // Navigate to lead edit page or show edit modal
        window.location.href = `/departments/sales/leads.html?edit=${leadId}`;
    }

    async convertToCustomer(leadId) {
        // Show conversion modal or navigate to conversion page
        window.location.href = `/departments/sales/customers.html?convert=${leadId}`;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.salesDashboard = new SalesDashboard();
});

// Make salesDashboard available globally for onclick handlers
window.salesDashboard = null;
