"""
Jira Data Dashboard - Backend API
Flask application that fetches data from Jira REST API
"""

import os
import random
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from functools import wraps
import json
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Jira Configuration - Set these as environment variables
JIRA_BASE_URL = os.environ.get('JIRA_BASE_URL', '')
JIRA_EMAIL = os.environ.get('JIRA_EMAIL', '')
JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN', '')

# Demo Mode - Set DEMO_MODE=true to use mock data
DEMO_MODE = os.environ.get('DEMO_MODE', 'false').lower() == 'true'

# ============== Demo Data ==============
DEMO_PROJECTS = [
    {"id": "10001", "key": "WEBAPP", "name": "웹 애플리케이션 개발", "projectTypeKey": "software"},
    {"id": "10002", "key": "MOBILE", "name": "모바일 앱 프로젝트", "projectTypeKey": "software"},
    {"id": "10003", "key": "INFRA", "name": "인프라 구축", "projectTypeKey": "service_desk"},
    {"id": "10004", "key": "DATA", "name": "데이터 분석 플랫폼", "projectTypeKey": "software"},
]

DEMO_USERS = ["김철수", "이영희", "박민수", "정수진", "최동현", "한지민", "Unassigned"]
DEMO_ISSUE_TYPES = ["Bug", "Task", "Story", "Epic", "Sub-task"]
DEMO_PRIORITIES = ["Highest", "High", "Medium", "Low", "Lowest"]
DEMO_STATUSES = [
    {"name": "To Do", "category": "To Do"},
    {"name": "In Progress", "category": "In Progress"},
    {"name": "In Review", "category": "In Progress"},
    {"name": "Done", "category": "Done"},
    {"name": "Backlog", "category": "To Do"},
]

DEMO_SUMMARIES = [
    "로그인 페이지 UI 개선",
    "API 응답 속도 최적화",
    "사용자 인증 버그 수정",
    "대시보드 차트 컴포넌트 개발",
    "데이터베이스 마이그레이션",
    "모바일 반응형 디자인 적용",
    "테스트 코드 작성",
    "CI/CD 파이프라인 구축",
    "보안 취약점 패치",
    "성능 모니터링 시스템 구축",
    "사용자 피드백 기능 추가",
    "알림 시스템 개발",
    "검색 기능 개선",
    "파일 업로드 기능 구현",
    "권한 관리 시스템 개발",
    "API 문서화",
    "에러 핸들링 개선",
    "캐싱 시스템 도입",
    "로깅 시스템 구축",
    "배치 작업 스케줄러 개발",
]

def generate_demo_issues(project_key=None, count=50):
    """Generate demo issues"""
    issues = []
    projects = [p for p in DEMO_PROJECTS if not project_key or p['key'] == project_key]

    for i in range(count):
        project = random.choice(projects)
        status = random.choice(DEMO_STATUSES)
        created_days_ago = random.randint(0, 60)
        updated_days_ago = random.randint(0, created_days_ago)

        issues.append({
            "key": f"{project['key']}-{100 + i}",
            "summary": random.choice(DEMO_SUMMARIES),
            "status": status["name"],
            "statusCategory": status["category"],
            "assignee": random.choice(DEMO_USERS),
            "reporter": random.choice([u for u in DEMO_USERS if u != "Unassigned"]),
            "priority": random.choice(DEMO_PRIORITIES),
            "issueType": random.choice(DEMO_ISSUE_TYPES),
            "project": project["name"],
            "created": (datetime.now() - timedelta(days=created_days_ago)).isoformat(),
            "updated": (datetime.now() - timedelta(days=updated_days_ago)).isoformat(),
        })

    return issues

def generate_demo_summary(project_key=None):
    """Generate demo dashboard summary"""
    issues = generate_demo_issues(project_key, count=87)

    stats = {
        "total": len(issues),
        "todo": 0,
        "inProgress": 0,
        "done": 0,
        "byPriority": {},
        "byType": {},
        "byAssignee": {},
        "recentlyCreated": 0,
        "recentlyUpdated": 0
    }

    now = datetime.now()
    week_ago = now - timedelta(days=7)

    for issue in issues:
        # Status category
        if issue["statusCategory"] == "To Do":
            stats["todo"] += 1
        elif issue["statusCategory"] == "In Progress":
            stats["inProgress"] += 1
        elif issue["statusCategory"] == "Done":
            stats["done"] += 1

        # Priority
        priority = issue["priority"]
        stats["byPriority"][priority] = stats["byPriority"].get(priority, 0) + 1

        # Issue Type
        issue_type = issue["issueType"]
        stats["byType"][issue_type] = stats["byType"].get(issue_type, 0) + 1

        # Assignee
        assignee = issue["assignee"]
        stats["byAssignee"][assignee] = stats["byAssignee"].get(assignee, 0) + 1

        # Recently created/updated
        created_date = datetime.fromisoformat(issue["created"])
        updated_date = datetime.fromisoformat(issue["updated"])

        if created_date > week_ago:
            stats["recentlyCreated"] += 1
        if updated_date > week_ago:
            stats["recentlyUpdated"] += 1

    return stats

# ============== Jira API Functions ==============
def get_jira_auth():
    """Get Jira authentication object"""
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

def get_jira_headers():
    """Get common headers for Jira API requests"""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def jira_request(endpoint, method='GET', params=None, data=None):
    """Make a request to Jira API"""
    url = f"{JIRA_BASE_URL}/rest/api/3/{endpoint}"

    try:
        response = requests.request(
            method,
            url,
            headers=get_jira_headers(),
            auth=get_jira_auth(),
            params=params,
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# ============== Routes ==============
@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    """Check if Jira is configured"""
    if DEMO_MODE:
        return jsonify({
            "configured": True,
            "jira_url": "https://demo.atlassian.net",
            "demo_mode": True
        })

    configured = bool(JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN)
    return jsonify({
        "configured": configured,
        "jira_url": JIRA_BASE_URL if configured else None,
        "demo_mode": False
    })

@app.route('/api/projects')
def get_projects():
    """Get all Jira projects"""
    if DEMO_MODE:
        return jsonify(DEMO_PROJECTS)

    result = jira_request('project')
    if isinstance(result, list):
        projects = [{
            "id": p.get("id"),
            "key": p.get("key"),
            "name": p.get("name"),
            "projectTypeKey": p.get("projectTypeKey")
        } for p in result]
        return jsonify(projects)
    return jsonify(result)

@app.route('/api/issues')
def get_issues():
    """Get issues with optional JQL filter"""
    jql = request.args.get('jql', 'ORDER BY created DESC')
    max_results = int(request.args.get('maxResults', 50))
    start_at = int(request.args.get('startAt', 0))

    if DEMO_MODE:
        # Parse project from JQL if present
        project_key = None
        if 'project = ' in jql:
            try:
                project_key = jql.split('project = ')[1].split()[0].strip()
            except:
                pass

        all_issues = generate_demo_issues(project_key, count=87)
        paginated_issues = all_issues[start_at:start_at + max_results]

        return jsonify({
            "issues": paginated_issues,
            "total": len(all_issues),
            "maxResults": max_results,
            "startAt": start_at
        })

    params = {
        'jql': jql,
        'maxResults': max_results,
        'startAt': start_at,
        'fields': 'summary,status,assignee,reporter,priority,created,updated,issuetype,project'
    }

    result = jira_request('search', params=params)

    if 'issues' in result:
        issues = []
        for issue in result['issues']:
            fields = issue.get('fields', {})
            issues.append({
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "status": fields.get("status", {}).get("name") if fields.get("status") else None,
                "statusCategory": fields.get("status", {}).get("statusCategory", {}).get("name") if fields.get("status") else None,
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
                "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
                "issueType": fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None,
                "project": fields.get("project", {}).get("name") if fields.get("project") else None,
                "created": fields.get("created"),
                "updated": fields.get("updated")
            })
        return jsonify({
            "issues": issues,
            "total": result.get("total", 0),
            "maxResults": result.get("maxResults", 0),
            "startAt": result.get("startAt", 0)
        })
    return jsonify(result)

@app.route('/api/issue/<issue_key>')
def get_issue(issue_key):
    """Get a specific issue by key"""
    if DEMO_MODE:
        # Generate a single demo issue
        project_key = issue_key.split('-')[0]
        return jsonify({
            "key": issue_key,
            "summary": random.choice(DEMO_SUMMARIES),
            "description": "이것은 데모 이슈입니다. 실제 Jira 연결 시 상세 정보가 표시됩니다.",
            "status": random.choice(DEMO_STATUSES)["name"],
            "assignee": random.choice(DEMO_USERS),
            "priority": random.choice(DEMO_PRIORITIES),
            "issueType": random.choice(DEMO_ISSUE_TYPES),
        })

    result = jira_request(f'issue/{issue_key}')
    return jsonify(result)

@app.route('/api/dashboard/summary')
def get_dashboard_summary():
    """Get summary statistics for dashboard"""
    project_key = request.args.get('project', '')

    if DEMO_MODE:
        return jsonify(generate_demo_summary(project_key if project_key else None))

    # Build JQL queries
    base_jql = f'project = {project_key}' if project_key else ''

    stats = {
        "total": 0,
        "todo": 0,
        "inProgress": 0,
        "done": 0,
        "byPriority": {},
        "byType": {},
        "byAssignee": {},
        "recentlyCreated": 0,
        "recentlyUpdated": 0
    }

    # Get all issues for the project
    jql = f'{base_jql} ORDER BY created DESC' if base_jql else 'ORDER BY created DESC'
    result = jira_request('search', params={
        'jql': jql,
        'maxResults': 1000,
        'fields': 'status,priority,issuetype,assignee,created,updated'
    })

    if 'issues' in result:
        stats['total'] = result.get('total', 0)

        now = datetime.now()
        week_ago = now - timedelta(days=7)

        for issue in result['issues']:
            fields = issue.get('fields', {})

            # Status category
            status_category = fields.get('status', {}).get('statusCategory', {}).get('name', 'Unknown')
            if status_category == 'To Do':
                stats['todo'] += 1
            elif status_category == 'In Progress':
                stats['inProgress'] += 1
            elif status_category == 'Done':
                stats['done'] += 1

            # Priority
            priority = fields.get('priority', {}).get('name', 'None') if fields.get('priority') else 'None'
            stats['byPriority'][priority] = stats['byPriority'].get(priority, 0) + 1

            # Issue Type
            issue_type = fields.get('issuetype', {}).get('name', 'Unknown') if fields.get('issuetype') else 'Unknown'
            stats['byType'][issue_type] = stats['byType'].get(issue_type, 0) + 1

            # Assignee
            assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
            stats['byAssignee'][assignee] = stats['byAssignee'].get(assignee, 0) + 1

            # Recently created/updated (last 7 days)
            created = fields.get('created', '')
            updated = fields.get('updated', '')

            if created:
                created_date = datetime.fromisoformat(created.replace('Z', '+00:00').split('+')[0])
                if created_date > week_ago:
                    stats['recentlyCreated'] += 1

            if updated:
                updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00').split('+')[0])
                if updated_date > week_ago:
                    stats['recentlyUpdated'] += 1

    return jsonify(stats)

@app.route('/api/sprint/active')
def get_active_sprint():
    """Get active sprint information"""
    if DEMO_MODE:
        return jsonify({
            "id": 1,
            "name": "Sprint 2024-01",
            "state": "active",
            "startDate": (datetime.now() - timedelta(days=7)).isoformat(),
            "endDate": (datetime.now() + timedelta(days=7)).isoformat(),
            "goal": "데모 스프린트 목표: 주요 기능 개발 완료"
        })

    board_id = request.args.get('boardId')

    if not board_id:
        # Try to get the first board
        boards_result = jira_request('board', params={'maxResults': 1})
        if 'values' in boards_result and boards_result['values']:
            board_id = boards_result['values'][0]['id']
        else:
            return jsonify({"error": "No board found"})

    # Get active sprint
    sprints_result = jira_request(f'board/{board_id}/sprint', params={'state': 'active'})

    if 'values' in sprints_result and sprints_result['values']:
        sprint = sprints_result['values'][0]
        return jsonify({
            "id": sprint.get("id"),
            "name": sprint.get("name"),
            "state": sprint.get("state"),
            "startDate": sprint.get("startDate"),
            "endDate": sprint.get("endDate"),
            "goal": sprint.get("goal")
        })

    return jsonify({"message": "No active sprint found"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    if DEMO_MODE:
        print("🎭 Running in DEMO MODE - Using mock data")

    app.run(host='0.0.0.0', port=port, debug=debug)
