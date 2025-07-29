/**
 * Development Department Dashboard JavaScript
 * Integrates with Development API endpoints for project and task management
 */

class DevelopmentDashboard {
    constructor() {
        this.apiClient = window.hrmsApi;
        this.currentUser = null;
        this.projects = [];
        this.tasks = [];
        this.team = [];
        this.devStats = {};
        this.sprints = [];
        
        this.init();
    }

    async init() {
        try {
            await this.loadCurrentUser();
            await this.loadDashboardData();
            this.setupEventListeners();
            this.renderDashboard();
        } catch (error) {
            console.error('Failed to initialize development dashboard:', error);
            ApiHelpers.handleApiError(error);
        }
    }

    async loadCurrentUser() {
        this.currentUser = window.currentUser || await this.apiClient.request('/users/me');
    }

    async loadDashboardData() {
        const loadingPromises = [
            this.loadProjects(),
            this.loadTasks(),
            this.loadTeam(),
            this.loadSprints(),
            this.loadDevStats()
        ];

        await Promise.all(loadingPromises);
    }

    async loadProjects() {
        try {
            this.projects = await this.apiClient.getProjects({ limit: 10 });
        } catch (error) {
            console.error('Failed to load projects:', error);
            this.projects = [];
        }
    }

    async loadTasks() {
        try {
            // Load tasks assigned to current user or team
            this.tasks = await this.apiClient.getTasks({ 
                assigned_to: this.currentUser?.id,
                limit: 20 
            });
        } catch (error) {
            console.error('Failed to load tasks:', error);
            this.tasks = [];
        }
    }

    async loadTeam() {
        try {
            this.team = await this.apiClient.getTeamMembers({ 
                department: 'Development',
                limit: 10 
            });
        } catch (error) {
            console.error('Failed to load team:', error);
            this.team = [];
        }
    }

    async loadSprints() {
        try {
            this.sprints = await this.apiClient.getSprints({ 
                status: 'active',
                limit: 5 
            });
        } catch (error) {
            console.error('Failed to load sprints:', error);
            this.sprints = [];
        }
    }

    async loadDevStats() {
        try {
            const [projectStats, taskStats, teamStats] = await Promise.all([
                this.apiClient.getProjectStats(),
                this.apiClient.getTaskStats(),
                this.apiClient.getTeamProductivity()
            ]);

            this.devStats = {
                ...projectStats,
                ...taskStats,
                ...teamStats
            };
        } catch (error) {
            console.error('Failed to load development stats:', error);
            this.devStats = {};
        }
    }

    renderDashboard() {
        this.renderStatsCards();
        this.renderActiveProjects();
        this.renderMyTasks();
        this.renderTeamOverview();
        this.renderSprintProgress();
        this.renderProductivityChart();
    }

    renderStatsCards() {
        const statsContainer = document.getElementById('dev-stats-cards');
        if (!statsContainer) return;

        const stats = [
            {
                title: 'Active Projects',
                value: this.devStats.active_projects || 0,
                icon: '🚀',
                color: 'primary'
            },
            {
                title: 'My Open Tasks',
                value: this.tasks.filter(t => ['pending', 'in_progress'].includes(t.status)).length,
                icon: '📋',
                color: 'warning'
            },
            {
                title: 'Code Reviews',
                value: this.devStats.pending_reviews || 0,
                icon: '👀',
                color: 'info'
            },
            {
                title: 'Team Velocity',
                value: `${this.devStats.team_velocity || 0} SP`,
                icon: '⚡',
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

    renderActiveProjects() {
        const projectsContainer = document.getElementById('active-projects');
        if (!projectsContainer) return;

        if (this.projects.length === 0) {
            projectsContainer.innerHTML = '<p class="text-muted">No active projects</p>';
            return;
        }

        projectsContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Project</th>
                            <th>Client</th>
                            <th>Progress</th>
                            <th>Team</th>
                            <th>Deadline</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.projects.slice(0, 5).map(project => `
                            <tr>
                                <td>
                                    <strong>${project.name}</strong><br>
                                    <small class="text-muted">${project.technology_stack?.join(', ') || 'N/A'}</small>
                                </td>
                                <td>${project.client_name || 'Internal'}</td>
                                <td>
                                    <div class="progress" style="height: 20px;">
                                        <div class="progress-bar bg-${this.getProgressColor(project.progress_percentage)}" 
                                             role="progressbar" 
                                             style="width: ${project.progress_percentage || 0}%">
                                            ${project.progress_percentage || 0}%
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <span class="badge bg-secondary">${project.team_size || 0} members</span>
                                </td>
                                <td>
                                    ${project.deadline ? ApiHelpers.formatDate(project.deadline) : 'No deadline'}
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="devDashboard.viewProject('${project.id}')">
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

    renderMyTasks() {
        const tasksContainer = document.getElementById('my-tasks');
        if (!tasksContainer) return;

        const myTasks = this.tasks.filter(task => 
            task.assigned_to === this.currentUser?.id || 
            task.assignee_id === this.currentUser?.id
        );

        if (myTasks.length === 0) {
            tasksContainer.innerHTML = '<p class="text-muted">No tasks assigned</p>';
            return;
        }

        tasksContainer.innerHTML = `
            <div class="list-group">
                ${myTasks.slice(0, 8).map(task => `
                    <div class="list-group-item d-flex justify-content-between align-items-start">
                        <div class="ms-2 me-auto">
                            <div class="fw-bold">${task.title}</div>
                            <small class="text-muted">${task.project_name || 'No project'}</small>
                            <div class="mt-1">
                                <span class="badge bg-${this.getTaskStatusColor(task.status)}">${task.status}</span>
                                <span class="badge bg-${this.getTaskPriorityColor(task.priority)}">${task.priority}</span>
                                ${task.story_points ? `<span class="badge bg-info">${task.story_points} SP</span>` : ''}
                            </div>
                        </div>
                        <div class="text-end">
                            <small class="text-muted">${task.due_date ? ApiHelpers.formatDate(task.due_date) : ''}</small><br>
                            <button class="btn btn-sm btn-outline-primary" onclick="devDashboard.viewTask('${task.id}')">
                                View
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderTeamOverview() {
        const teamContainer = document.getElementById('team-overview');
        if (!teamContainer) return;

        if (this.team.length === 0) {
            teamContainer.innerHTML = '<p class="text-muted">No team members found</p>';
            return;
        }

        teamContainer.innerHTML = `
            <div class="row">
                ${this.team.slice(0, 6).map(member => `
                    <div class="col-md-4 mb-3">
                        <div class="card">
                            <div class="card-body text-center">
                                <div class="mb-2">
                                    <div class="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center" 
                                         style="width: 50px; height: 50px;">
                                        ${member.full_name?.charAt(0) || '?'}
                                    </div>
                                </div>
                                <h6 class="card-title mb-1">${member.full_name}</h6>
                                <small class="text-muted">${member.position}</small>
                                <div class="mt-2">
                                    <span class="badge bg-${this.getStatusColor(member.status)}">${member.status}</span>
                                </div>
                                <div class="mt-2">
                                    <small class="text-muted">
                                        ${member.active_tasks || 0} active tasks
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderSprintProgress() {
        const sprintContainer = document.getElementById('sprint-progress');
        if (!sprintContainer) return;

        if (this.sprints.length === 0) {
            sprintContainer.innerHTML = '<p class="text-muted">No active sprints</p>';
            return;
        }

        const currentSprint = this.sprints[0]; // Assume first is current
        
        sprintContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Current Sprint: ${currentSprint.name}</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Duration:</strong> ${ApiHelpers.formatDate(currentSprint.start_date)} - ${ApiHelpers.formatDate(currentSprint.end_date)}</p>
                            <p><strong>Story Points:</strong> ${currentSprint.completed_points || 0} / ${currentSprint.total_points || 0}</p>
                        </div>
                        <div class="col-md-6">
                            <div class="progress mb-2">
                                <div class="progress-bar" role="progressbar" 
                                     style="width: ${this.calculateSprintProgress(currentSprint)}%">
                                    ${this.calculateSprintProgress(currentSprint)}%
                                </div>
                            </div>
                            <small class="text-muted">${currentSprint.days_remaining || 0} days remaining</small>
                        </div>
                    </div>
                    <div class="mt-3">
                        <div class="row text-center">
                            <div class="col-3">
                                <div class="h5 text-secondary">${currentSprint.todo_tasks || 0}</div>
                                <small class="text-muted">To Do</small>
                            </div>
                            <div class="col-3">
                                <div class="h5 text-primary">${currentSprint.in_progress_tasks || 0}</div>
                                <small class="text-muted">In Progress</small>
                            </div>
                            <div class="col-3">
                                <div class="h5 text-warning">${currentSprint.review_tasks || 0}</div>
                                <small class="text-muted">Review</small>
                            </div>
                            <div class="col-3">
                                <div class="h5 text-success">${currentSprint.done_tasks || 0}</div>
                                <small class="text-muted">Done</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderProductivityChart() {
        const chartContainer = document.getElementById('productivity-chart');
        if (!chartContainer) return;

        // Simple productivity indicators without external charting library
        const productivity = this.devStats.weekly_productivity || [];
        const maxValue = Math.max(...productivity, 1);

        chartContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Team Productivity (Last 7 Days)</h6>
                </div>
                <div class="card-body">
                    <div class="d-flex align-items-end justify-content-between" style="height: 150px;">
                        ${productivity.map((value, index) => {
                            const height = (value / maxValue) * 100;
                            const day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index];
                            return `
                                <div class="text-center" style="flex: 1;">
                                    <div class="bg-primary mb-2" 
                                         style="height: ${height}%; width: 80%; margin: 0 auto; border-radius: 3px;"
                                         title="${value} story points">
                                    </div>
                                    <small class="text-muted">${day}</small>
                                </div>
                            `;
                        }).join('')}
                    </div>
                    <div class="mt-3 text-center">
                        <small class="text-muted">Story points completed per day</small>
                    </div>
                </div>
            </div>
        `;
    }

    getProgressColor(percentage) {
        if (percentage >= 80) return 'success';
        if (percentage >= 60) return 'info';
        if (percentage >= 40) return 'warning';
        return 'danger';
    }

    getTaskStatusColor(status) {
        const colors = {
            'pending': 'secondary',
            'in_progress': 'primary',
            'review': 'warning',
            'testing': 'info',
            'completed': 'success',
            'blocked': 'danger'
        };
        return colors[status] || 'secondary';
    }

    getTaskPriorityColor(priority) {
        const colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'urgent': 'dark'
        };
        return colors[priority] || 'secondary';
    }

    getStatusColor(status) {
        const colors = {
            'active': 'success',
            'busy': 'warning',
            'away': 'secondary',
            'offline': 'dark'
        };
        return colors[status] || 'secondary';
    }

    calculateSprintProgress(sprint) {
        if (!sprint.total_points || sprint.total_points === 0) return 0;
        return Math.round((sprint.completed_points / sprint.total_points) * 100);
    }

    async viewProject(projectId) {
        try {
            const project = await this.apiClient.getProjectById(projectId);
            this.showProjectModal(project);
        } catch (error) {
            ApiHelpers.handleApiError(error);
        }
    }

    async viewTask(taskId) {
        try {
            const task = await this.apiClient.getTaskById(taskId);
            this.showTaskModal(task);
        } catch (error) {
            ApiHelpers.handleApiError(error);
        }
    }

    showProjectModal(project) {
        const modalHTML = `
            <div class="modal fade" id="projectModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Project - ${project.name}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Project Information</h6>
                                    <p><strong>Name:</strong> ${project.name}</p>
                                    <p><strong>Client:</strong> ${project.client_name || 'Internal'}</p>
                                    <p><strong>Status:</strong> <span class="badge bg-${this.getProjectStatusColor(project.status)}">${project.status}</span></p>
                                    <p><strong>Priority:</strong> <span class="badge bg-${this.getTaskPriorityColor(project.priority)}">${project.priority}</span></p>
                                    <p><strong>Budget:</strong> ${project.budget ? ApiHelpers.formatCurrency(project.budget) : 'Not set'}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>Progress & Timeline</h6>
                                    <p><strong>Progress:</strong> ${project.progress_percentage || 0}%</p>
                                    <p><strong>Start Date:</strong> ${ApiHelpers.formatDate(project.start_date)}</p>
                                    <p><strong>Deadline:</strong> ${project.deadline ? ApiHelpers.formatDate(project.deadline) : 'No deadline'}</p>
                                    <p><strong>Team Size:</strong> ${project.team_size || 0} members</p>
                                    <p><strong>Technology:</strong> ${project.technology_stack?.join(', ') || 'Not specified'}</p>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-12">
                                    <h6>Description</h6>
                                    <p>${project.description}</p>
                                    ${project.requirements ? `<h6>Requirements</h6><p>${project.requirements}</p>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" onclick="devDashboard.editProject('${project.id}')">Edit Project</button>
                            <button type="button" class="btn btn-info" onclick="devDashboard.viewProjectTasks('${project.id}')">View Tasks</button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.showModal(modalHTML, 'projectModal');
    }

    showTaskModal(task) {
        // Similar implementation for task details
        console.log('Task details:', task);
    }

    getProjectStatusColor(status) {
        const colors = {
            'planning': 'secondary',
            'active': 'primary',
            'on_hold': 'warning',
            'completed': 'success',
            'cancelled': 'danger'
        };
        return colors[status] || 'secondary';
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
        const refreshBtn = document.getElementById('refresh-dev-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboardData().then(() => this.renderDashboard());
            });
        }

        // Quick actions
        const quickActions = {
            'create-project': () => this.createProject(),
            'create-task': () => this.createTask(),
            'start-sprint': () => this.startSprint(),
            'view-backlog': () => this.viewBacklog()
        };

        Object.entries(quickActions).forEach(([id, handler]) => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('click', handler);
            }
        });

        // Task status updates
        this.setupTaskStatusHandlers();
    }

    setupTaskStatusHandlers() {
        // Add drag and drop or quick status update functionality
        // This would integrate with the task management API
    }

    createProject() {
        window.location.href = '/departments/development/projects.html?action=create';
    }

    createTask() {
        window.location.href = '/departments/development/tasks.html?action=create';
    }

    startSprint() {
        window.location.href = '/departments/development/sprints.html?action=start';
    }

    viewBacklog() {
        window.location.href = '/departments/development/backlog.html';
    }

    editProject(projectId) {
        window.location.href = `/departments/development/projects.html?edit=${projectId}`;
    }

    viewProjectTasks(projectId) {
        window.location.href = `/departments/development/tasks.html?project=${projectId}`;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.devDashboard = new DevelopmentDashboard();
});

// Make devDashboard available globally
window.devDashboard = null;
