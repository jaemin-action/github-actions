"""
Jira Data Dashboard - Backend API
Flask application that fetches data from Jira REST API
"""

import os
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from functools import wraps
import json

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Jira Configuration - Set these as environment variables
JIRA_BASE_URL = os.environ.get('JIRA_BASE_URL', '')
JIRA_EMAIL = os.environ.get('JIRA_EMAIL', '')
JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN', '')

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

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    """Check if Jira is configured"""
    configured = bool(JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN)
    return jsonify({
        "configured": configured,
        "jira_url": JIRA_BASE_URL if configured else None
    })

@app.route('/api/projects')
def get_projects():
    """Get all Jira projects"""
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
    max_results = request.args.get('maxResults', 50)
    start_at = request.args.get('startAt', 0)

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
    result = jira_request(f'issue/{issue_key}')
    return jsonify(result)

@app.route('/api/dashboard/summary')
def get_dashboard_summary():
    """Get summary statistics for dashboard"""
    project_key = request.args.get('project', '')

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
    app.run(host='0.0.0.0', port=port, debug=debug)
