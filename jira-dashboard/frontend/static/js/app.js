/**
 * Jira Dashboard - Frontend Application
 */

// Global state
const state = {
    currentView: 'dashboard',
    projects: [],
    selectedProject: '',
    currentPage: 0,
    pageSize: 20,
    totalIssues: 0,
    charts: {}
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    checkConfiguration();
    loadProjects();
    loadDashboardData();
});

// Navigation
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            switchView(view);
        });
    });
}

function switchView(viewName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}View`).classList.add('active');

    // Update title
    const titles = {
        dashboard: '대시보드',
        issues: '이슈 목록',
        projects: '프로젝트'
    };
    document.getElementById('pageTitle').textContent = titles[viewName];

    // Load data based on view
    state.currentView = viewName;
    if (viewName === 'issues') {
        loadIssues();
    } else if (viewName === 'projects') {
        loadProjects(true);
    }
}

// API calls
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`/api/${endpoint}`);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { error: error.message };
    }
}

// Check Jira configuration
async function checkConfiguration() {
    const config = await fetchAPI('config');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');

    if (config.configured) {
        statusDot.classList.add('connected');
        statusText.textContent = 'Jira 연결됨';
    } else {
        statusDot.classList.add('error');
        statusText.textContent = '설정 필요';
        document.getElementById('configModal').classList.add('active');
    }
}

function closeConfigModal() {
    document.getElementById('configModal').classList.remove('active');
}

// Load projects
async function loadProjects(showInView = false) {
    const projects = await fetchAPI('projects');

    if (Array.isArray(projects)) {
        state.projects = projects;

        // Update project filter dropdown
        const select = document.getElementById('projectFilter');
        select.innerHTML = '<option value="">모든 프로젝트</option>';
        projects.forEach(project => {
            select.innerHTML += `<option value="${project.key}">${project.name}</option>`;
        });

        select.addEventListener('change', (e) => {
            state.selectedProject = e.target.value;
            refreshData();
        });

        // Update projects view if needed
        if (showInView) {
            renderProjectsGrid(projects);
        }
    }
}

function renderProjectsGrid(projects) {
    const grid = document.getElementById('projectsGrid');

    if (!projects.length) {
        grid.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                </svg>
                <h3>프로젝트가 없습니다</h3>
                <p>Jira에서 접근 가능한 프로젝트가 없습니다.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = projects.map(project => `
        <div class="project-card" onclick="selectProject('${project.key}')">
            <div class="project-header">
                <div class="project-avatar">${project.key.substring(0, 2)}</div>
                <div class="project-info">
                    <h3>${project.name}</h3>
                    <span class="project-key">${project.key}</span>
                </div>
            </div>
            <span class="project-type">${project.projectTypeKey || 'software'}</span>
        </div>
    `).join('');
}

function selectProject(projectKey) {
    state.selectedProject = projectKey;
    document.getElementById('projectFilter').value = projectKey;
    switchView('dashboard');
    refreshData();
}

// Load dashboard data
async function loadDashboardData() {
    const projectParam = state.selectedProject ? `?project=${state.selectedProject}` : '';
    const summary = await fetchAPI(`dashboard/summary${projectParam}`);

    if (!summary.error) {
        // Update stat cards
        document.getElementById('totalIssues').textContent = summary.total || 0;
        document.getElementById('todoIssues').textContent = summary.todo || 0;
        document.getElementById('inProgressIssues').textContent = summary.inProgress || 0;
        document.getElementById('doneIssues').textContent = summary.done || 0;

        // Update charts
        updateCharts(summary);

        // Update assignee table
        updateAssigneeTable(summary.byAssignee, summary.total);
    }
}

// Charts
function updateCharts(data) {
    // Destroy existing charts
    Object.values(state.charts).forEach(chart => chart.destroy());

    // Issue Type Chart
    const typeCtx = document.getElementById('issueTypeChart').getContext('2d');
    state.charts.type = new Chart(typeCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data.byType),
            datasets: [{
                data: Object.values(data.byType),
                backgroundColor: [
                    '#0052CC',
                    '#00B8D9',
                    '#36B37E',
                    '#FFAB00',
                    '#FF5630',
                    '#6554C0'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 16,
                        usePointStyle: true
                    }
                }
            }
        }
    });

    // Priority Chart
    const priorityCtx = document.getElementById('priorityChart').getContext('2d');
    const priorityColors = {
        'Highest': '#FF5630',
        'High': '#FF7452',
        'Medium': '#FFAB00',
        'Low': '#36B37E',
        'Lowest': '#00875A',
        'None': '#97A0AF'
    };
    state.charts.priority = new Chart(priorityCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(data.byPriority),
            datasets: [{
                data: Object.values(data.byPriority),
                backgroundColor: Object.keys(data.byPriority).map(p => priorityColors[p] || '#97A0AF'),
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });

    // Status Chart
    const statusCtx = document.getElementById('statusChart').getContext('2d');
    state.charts.status = new Chart(statusCtx, {
        type: 'pie',
        data: {
            labels: ['할 일', '진행 중', '완료'],
            datasets: [{
                data: [data.todo, data.inProgress, data.done],
                backgroundColor: ['#DFE1E6', '#0052CC', '#00875A'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 16,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function updateAssigneeTable(assigneeData, total) {
    const tbody = document.getElementById('assigneeTableBody');

    if (!assigneeData || Object.keys(assigneeData).length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="empty-state">담당자 데이터가 없습니다</td>
            </tr>
        `;
        return;
    }

    // Sort by issue count
    const sorted = Object.entries(assigneeData)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    tbody.innerHTML = sorted.map(([name, count]) => {
        const percentage = total ? ((count / total) * 100).toFixed(1) : 0;
        return `
            <tr>
                <td>${name}</td>
                <td>${count}</td>
                <td>
                    <div class="progress-bar" style="width: 100px; display: inline-block; vertical-align: middle;">
                        <div class="progress-fill" style="width: ${percentage}%"></div>
                    </div>
                    <span style="margin-left: 8px;">${percentage}%</span>
                </td>
            </tr>
        `;
    }).join('');
}

// Issues
async function loadIssues() {
    const tbody = document.getElementById('issuesTableBody');
    tbody.innerHTML = '<tr><td colspan="7" class="loading"><div class="spinner"></div></td></tr>';

    let jql = document.getElementById('jqlInput').value || 'ORDER BY created DESC';
    if (state.selectedProject) {
        jql = `project = ${state.selectedProject} AND ${jql}`;
    }

    const params = new URLSearchParams({
        jql: jql,
        maxResults: state.pageSize,
        startAt: state.currentPage * state.pageSize
    });

    const result = await fetchAPI(`issues?${params}`);

    if (result.issues) {
        state.totalIssues = result.total;
        renderIssuesTable(result.issues);
        renderPagination();
    } else {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    ${result.error || '이슈를 불러올 수 없습니다'}
                </td>
            </tr>
        `;
    }
}

function renderIssuesTable(issues) {
    const tbody = document.getElementById('issuesTableBody');

    if (!issues.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">이슈가 없습니다</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = issues.map(issue => {
        const statusClass = getStatusClass(issue.statusCategory);
        const priorityClass = getPriorityClass(issue.priority);
        const createdDate = issue.created ? new Date(issue.created).toLocaleDateString('ko-KR') : '-';

        return `
            <tr>
                <td><a href="#" class="issue-link" onclick="viewIssue('${issue.key}')">${issue.key}</a></td>
                <td>${issue.summary || '-'}</td>
                <td><span class="status-badge ${statusClass}">${issue.status || '-'}</span></td>
                <td>${issue.assignee || '-'}</td>
                <td>
                    <span class="priority-badge">
                        <span class="priority-dot ${priorityClass}"></span>
                        ${issue.priority || '-'}
                    </span>
                </td>
                <td>${issue.issueType || '-'}</td>
                <td>${createdDate}</td>
            </tr>
        `;
    }).join('');
}

function getStatusClass(statusCategory) {
    switch (statusCategory) {
        case 'To Do': return 'todo';
        case 'In Progress': return 'in-progress';
        case 'Done': return 'done';
        default: return '';
    }
}

function getPriorityClass(priority) {
    switch (priority?.toLowerCase()) {
        case 'highest': return 'highest';
        case 'high': return 'high';
        case 'medium': return 'medium';
        case 'low': return 'low';
        case 'lowest': return 'lowest';
        default: return '';
    }
}

function renderPagination() {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(state.totalIssues / state.pageSize);

    pagination.innerHTML = `
        <button onclick="changePage(${state.currentPage - 1})" ${state.currentPage === 0 ? 'disabled' : ''}>
            이전
        </button>
        <span class="page-info">${state.currentPage + 1} / ${totalPages} (총 ${state.totalIssues}개)</span>
        <button onclick="changePage(${state.currentPage + 1})" ${state.currentPage >= totalPages - 1 ? 'disabled' : ''}>
            다음
        </button>
    `;
}

function changePage(page) {
    if (page >= 0 && page < Math.ceil(state.totalIssues / state.pageSize)) {
        state.currentPage = page;
        loadIssues();
    }
}

function searchIssues() {
    state.currentPage = 0;
    loadIssues();
}

function viewIssue(issueKey) {
    // Could open a modal or redirect to Jira
    const jiraUrl = document.querySelector('.status-text').textContent === 'Jira 연결됨';
    if (jiraUrl) {
        // This would need the base URL from config
        console.log('View issue:', issueKey);
    }
}

// Refresh data
function refreshData() {
    if (state.currentView === 'dashboard') {
        loadDashboardData();
    } else if (state.currentView === 'issues') {
        loadIssues();
    } else if (state.currentView === 'projects') {
        loadProjects(true);
    }
}

// Handle Enter key in JQL input
document.getElementById('jqlInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchIssues();
    }
});
