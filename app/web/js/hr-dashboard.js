/**
 * HR Department Dashboard JavaScript
 * Integrates with HR API endpoints for recruitment, policies, and employee management
 */

class HRDashboard {
    constructor() {
        this.apiClient = window.hrmsApi;
        this.currentUser = null;
        this.jobPostings = [];
        this.applications = [];
        this.interviews = [];
        this.employees = [];
        this.hrStats = {};
        
        this.init();
    }

    async init() {
        try {
            await this.loadCurrentUser();
            await this.loadDashboardData();
            this.setupEventListeners();
            this.renderDashboard();
        } catch (error) {
            console.error('Failed to initialize HR dashboard:', error);
            ApiHelpers.handleApiError(error);
        }
    }

    async loadCurrentUser() {
        this.currentUser = window.currentUser || await this.apiClient.request('/users/me');
    }

    async loadDashboardData() {
        const loadingPromises = [
            this.loadJobPostings(),
            this.loadApplications(),
            this.loadInterviews(),
            this.loadEmployees(),
            this.loadHRStats()
        ];

        await Promise.all(loadingPromises);
    }

    async loadJobPostings() {
        try {
            this.jobPostings = await this.apiClient.getJobPostings({ limit: 10 });
        } catch (error) {
            console.error('Failed to load job postings:', error);
            this.jobPostings = [];
        }
    }

    async loadApplications() {
        try {
            this.applications = await this.apiClient.getJobApplications({ limit: 10 });
        } catch (error) {
            console.error('Failed to load applications:', error);
            this.applications = [];
        }
    }

    async loadInterviews() {
        try {
            const today = new Date().toISOString().split('T')[0];
            this.interviews = await this.apiClient.getInterviews({ 
                start_date: today,
                limit: 10 
            });
        } catch (error) {
            console.error('Failed to load interviews:', error);
            this.interviews = [];
        }
    }

    async loadEmployees() {
        try {
            this.employees = await this.apiClient.getEmployees({ limit: 10 });
        } catch (error) {
            console.error('Failed to load employees:', error);
            this.employees = [];
        }
    }

    async loadHRStats() {
        try {
            // Get various stats from different endpoints
            const [jobStats, appStats, empStats] = await Promise.all([
                this.apiClient.getJobPostingStats(),
                this.apiClient.getApplicationStats(),
                this.apiClient.getEmployeeStats()
            ]);

            this.hrStats = {
                ...jobStats,
                ...appStats,
                ...empStats
            };
        } catch (error) {
            console.error('Failed to load HR stats:', error);
            this.hrStats = {};
        }
    }

    renderDashboard() {
        this.renderStatsCards();
        this.renderActiveJobPostings();
        this.renderRecentApplications();
        this.renderTodaysInterviews();
        this.renderRecentEmployees();
        this.renderRecruitmentFunnel();
    }

    renderStatsCards() {
        const statsContainer = document.getElementById('hr-stats-cards');
        if (!statsContainer) return;

        const stats = [
            {
                title: 'Active Job Postings',
                value: this.hrStats.active_jobs || 0,
                icon: '📋',
                color: 'primary'
            },
            {
                title: 'Pending Applications',
                value: this.hrStats.pending_applications || 0,
                icon: '📄',
                color: 'warning'
            },
            {
                title: 'Today\'s Interviews',
                value: this.interviews.length,
                icon: '🎤',
                color: 'info'
            },
            {
                title: 'Total Employees',
                value: this.hrStats.total_employees || 0,
                icon: '👥',
                color: 'success'
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

    renderActiveJobPostings() {
        const jobsContainer = document.getElementById('active-job-postings');
        if (!jobsContainer) return;

        if (this.jobPostings.length === 0) {
            jobsContainer.innerHTML = '<p class="text-muted">No active job postings</p>';
            return;
        }

        jobsContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Position</th>
                            <th>Department</th>
                            <th>Applications</th>
                            <th>Status</th>
                            <th>Posted</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.jobPostings.slice(0, 5).map(job => `
                            <tr>
                                <td>
                                    <strong>${job.title}</strong><br>
                                    <small class="text-muted">${job.employment_type}</small>
                                </td>
                                <td>${job.department}</td>
                                <td>
                                    <span class="badge bg-primary">${job.application_count || 0}</span>
                                </td>
                                <td>
                                    <span class="badge bg-${this.getJobStatusColor(job.status)}">
                                        ${job.status}
                                    </span>
                                </td>
                                <td>
                                    ${ApiHelpers.formatDate(job.posted_date)}
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="hrDashboard.viewJobPosting('${job.id}')">
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

    renderRecentApplications() {
        const appsContainer = document.getElementById('recent-applications');
        if (!appsContainer) return;

        if (this.applications.length === 0) {
            appsContainer.innerHTML = '<p class="text-muted">No recent applications</p>';
            return;
        }

        appsContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Candidate</th>
                            <th>Position</th>
                            <th>Status</th>
                            <th>Applied</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.applications.slice(0, 5).map(app => `
                            <tr>
                                <td>
                                    <strong>${app.candidate_name}</strong><br>
                                    <small class="text-muted">${app.email}</small>
                                </td>
                                <td>${app.job_title || 'N/A'}</td>
                                <td>
                                    <span class="badge bg-${this.getApplicationStatusColor(app.status)}">
                                        ${app.status}
                                    </span>
                                </td>
                                <td>
                                    ${ApiHelpers.formatDate(app.applied_date)}
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="hrDashboard.viewApplication('${app.id}')">
                                        Review
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderTodaysInterviews() {
        const interviewsContainer = document.getElementById('todays-interviews');
        if (!interviewsContainer) return;

        if (this.interviews.length === 0) {
            interviewsContainer.innerHTML = '<p class="text-muted">No interviews scheduled for today</p>';
            return;
        }

        interviewsContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Candidate</th>
                            <th>Position</th>
                            <th>Interviewer</th>
                            <th>Type</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.interviews.map(interview => `
                            <tr>
                                <td>
                                    <strong>${ApiHelpers.formatTime(interview.scheduled_time)}</strong>
                                </td>
                                <td>
                                    ${interview.candidate_name}<br>
                                    <small class="text-muted">${interview.candidate_email}</small>
                                </td>
                                <td>${interview.job_title || 'N/A'}</td>
                                <td>${interview.interviewer_name}</td>
                                <td>
                                    <span class="badge bg-info">${interview.interview_type}</span>
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="hrDashboard.viewInterview('${interview.id}')">
                                        Details
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderRecentEmployees() {
        const employeesContainer = document.getElementById('recent-employees');
        if (!employeesContainer) return;

        if (this.employees.length === 0) {
            employeesContainer.innerHTML = '<p class="text-muted">No employees found</p>';
            return;
        }

        employeesContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Department</th>
                            <th>Position</th>
                            <th>Status</th>
                            <th>Join Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.employees.slice(0, 5).map(emp => `
                            <tr>
                                <td>
                                    <strong>${emp.full_name}</strong><br>
                                    <small class="text-muted">${emp.email}</small>
                                </td>
                                <td>${emp.department}</td>
                                <td>${emp.position}</td>
                                <td>
                                    <span class="badge bg-${this.getEmployeeStatusColor(emp.status)}">
                                        ${emp.status}
                                    </span>
                                </td>
                                <td>
                                    ${ApiHelpers.formatDate(emp.hire_date)}
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="hrDashboard.viewEmployee('${emp.id}')">
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

    renderRecruitmentFunnel() {
        const funnelContainer = document.getElementById('recruitment-funnel');
        if (!funnelContainer) return;

        const stages = [
            { name: 'Applied', count: this.hrStats.total_applications || 0, color: 'secondary' },
            { name: 'Under Review', count: this.hrStats.under_review || 0, color: 'primary' },
            { name: 'Interview Scheduled', count: this.hrStats.interview_scheduled || 0, color: 'info' },
            { name: 'Final Round', count: this.hrStats.final_round || 0, color: 'warning' },
            { name: 'Offer Extended', count: this.hrStats.offer_extended || 0, color: 'success' },
            { name: 'Hired', count: this.hrStats.hired || 0, color: 'dark' }
        ];

        funnelContainer.innerHTML = `
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

    getJobStatusColor(status) {
        const colors = {
            'active': 'success',
            'paused': 'warning',
            'closed': 'danger',
            'draft': 'secondary'
        };
        return colors[status] || 'secondary';
    }

    getApplicationStatusColor(status) {
        const colors = {
            'applied': 'secondary',
            'under_review': 'primary',
            'interview_scheduled': 'info',
            'interview_completed': 'warning',
            'offer_extended': 'success',
            'hired': 'dark',
            'rejected': 'danger',
            'withdrawn': 'secondary'
        };
        return colors[status] || 'secondary';
    }

    getEmployeeStatusColor(status) {
        const colors = {
            'active': 'success',
            'inactive': 'warning',
            'terminated': 'danger',
            'on_leave': 'info'
        };
        return colors[status] || 'secondary';
    }

    async viewJobPosting(jobId) {
        try {
            const job = await this.apiClient.getJobPostingById(jobId);
            this.showJobPostingModal(job);
        } catch (error) {
            ApiHelpers.handleApiError(error);
        }
    }

    async viewApplication(applicationId) {
        try {
            const application = await this.apiClient.getJobApplicationById(applicationId);
            this.showApplicationModal(application);
        } catch (error) {
            ApiHelpers.handleApiError(error);
        }
    }

    async viewInterview(interviewId) {
        try {
            const interview = await this.apiClient.getInterviewById(interviewId);
            this.showInterviewModal(interview);
        } catch (error) {
            ApiHelpers.handleApiError(error);
        }
    }

    async viewEmployee(employeeId) {
        try {
            const employee = await this.apiClient.getEmployeeById(employeeId);
            this.showEmployeeModal(employee);
        } catch (error) {
            ApiHelpers.handleApiError(error);
        }
    }

    showJobPostingModal(job) {
        const modalHTML = `
            <div class="modal fade" id="jobModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Job Posting - ${job.title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Basic Information</h6>
                                    <p><strong>Title:</strong> ${job.title}</p>
                                    <p><strong>Department:</strong> ${job.department}</p>
                                    <p><strong>Employment Type:</strong> ${job.employment_type}</p>
                                    <p><strong>Experience Level:</strong> ${job.experience_level}</p>
                                    <p><strong>Status:</strong> <span class="badge bg-${this.getJobStatusColor(job.status)}">${job.status}</span></p>
                                </div>
                                <div class="col-md-6">
                                    <h6>Job Details</h6>
                                    <p><strong>Posted Date:</strong> ${ApiHelpers.formatDate(job.posted_date)}</p>
                                    <p><strong>Application Deadline:</strong> ${ApiHelpers.formatDate(job.application_deadline)}</p>
                                    <p><strong>Salary Range:</strong> ${job.salary_range}</p>
                                    <p><strong>Location:</strong> ${job.location}</p>
                                    <p><strong>Applications:</strong> ${job.application_count || 0}</p>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-12">
                                    <h6>Job Description</h6>
                                    <p>${job.description}</p>
                                    <h6>Requirements</h6>
                                    <p>${job.requirements}</p>
                                    ${job.benefits ? `<h6>Benefits</h6><p>${job.benefits}</p>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" onclick="hrDashboard.editJobPosting('${job.id}')">Edit</button>
                            <button type="button" class="btn btn-info" onclick="hrDashboard.viewApplications('${job.id}')">View Applications</button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.showModal(modalHTML, 'jobModal');
    }

    showApplicationModal(application) {
        // Similar implementation for application details
        console.log('Application details:', application);
    }

    showInterviewModal(interview) {
        // Similar implementation for interview details
        console.log('Interview details:', interview);
    }

    showEmployeeModal(employee) {
        // Similar implementation for employee details
        console.log('Employee details:', employee);
    }

    showModal(modalHTML, modalId) {
        const existingModal = document.getElementById(modalId);
        if (existingModal) existingModal.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
    }

    setupEventListeners() {
        // Refresh dashboard
        const refreshBtn = document.getElementById('refresh-hr-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboardData().then(() => this.renderDashboard());
            });
        }

        // Quick actions
        const quickActions = {
            'create-job-posting': () => this.createJobPosting(),
            'schedule-interview': () => this.scheduleInterview(),
            'add-employee': () => this.addEmployee(),
            'view-policies': () => this.viewPolicies()
        };

        Object.entries(quickActions).forEach(([id, handler]) => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('click', handler);
            }
        });
    }

    createJobPosting() {
        window.location.href = '/departments/hr/job-postings.html?action=create';
    }

    scheduleInterview() {
        window.location.href = '/departments/hr/interviews.html?action=schedule';
    }

    addEmployee() {
        window.location.href = '/departments/hr/employees.html?action=add';
    }

    viewPolicies() {
        window.location.href = '/departments/hr/policies.html';
    }

    editJobPosting(jobId) {
        window.location.href = `/departments/hr/job-postings.html?edit=${jobId}`;
    }

    viewApplications(jobId) {
        window.location.href = `/departments/hr/applications.html?job=${jobId}`;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.hrDashboard = new HRDashboard();
});

// Make hrDashboard available globally
window.hrDashboard = null;
