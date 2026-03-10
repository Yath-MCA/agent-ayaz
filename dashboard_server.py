"""
AyazDy - Task Queue Web Dashboard
Allows users to select projects and trigger task queue execution
Ports and URLs are configured via environment variables
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import json
from pathlib import Path
import asyncio
import os

# Import configuration
from config.settings import config

app = FastAPI(title="AyazDy Task Queue Dashboard")

# Get configuration from settings
API_URL = config.service_urls.queue_api
DASHBOARD_PORT = config.service_ports.dashboard
QUEUE_ROOT = Path(os.getenv("QUEUE_PATH", "/app/agent-task"))

# Get list of projects
def get_projects():
    """Scan queue directories for projects"""
    projects = []
    queue_dir = QUEUE_ROOT / "queue"
    
    if queue_dir.exists():
        for item in queue_dir.iterdir():
            if item.is_dir():
                projects.append(item.name)
    
    # Also check for files directly in queue (default project)
    files = [f.name for f in queue_dir.glob("*.yaml") if f.is_file()]
    if files:
        projects.insert(0, "default")
    
    return sorted(set(projects)) if projects else ["default"]

# Get tasks for a project
def get_project_tasks(project="default"):
    """Get tasks queued for a specific project"""
    queue_dir = QUEUE_ROOT / "queue"
    tasks = []
    
    if project == "default":
        # Root level tasks
        for item in queue_dir.glob("*.yaml"):
            if item.is_file():
                tasks.append(item.name)
    else:
        # Project directory
        project_dir = queue_dir / project
        if project_dir.exists():
            for item in project_dir.glob("*.yaml"):
                if item.is_file():
                    tasks.append(item.name)
    
    return sorted(tasks)

@app.get("/")
async def dashboard():
    """Main dashboard HTML"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 AyazDy Task Queue Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 800px;
            width: 100%;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .info-box {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
            color: #555;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 10px;
            font-size: 1.05em;
        }
        
        select, input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 30px;
        }
        
        button {
            flex: 1;
            padding: 14px;
            font-size: 1.05em;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-trigger {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-trigger:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn-status {
            background: #f0f0f0;
            color: #333;
        }
        
        .btn-status:hover {
            background: #e0e0e0;
        }
        
        .status-box {
            background: #f9f9f9;
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
            display: none;
        }
        
        .status-box.show {
            display: block;
        }
        
        .status-item {
            padding: 10px;
            margin-bottom: 10px;
            border-left: 3px solid #667eea;
            background: white;
            border-radius: 4px;
        }
        
        .status-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .status-value {
            color: #333;
            font-weight: 600;
            font-size: 1.2em;
            margin-top: 5px;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f0f0f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .success {
            color: #22c55e;
        }
        
        .error {
            color: #ef4444;
        }
        
        .warning {
            color: #f59e0b;
        }
        
        .ports-info {
            background: #f0f9ff;
            border: 1px solid #0284c7;
            border-radius: 8px;
            padding: 15px;
            margin-top: 30px;
            font-size: 0.95em;
            color: #0c4a6e;
        }
        
        .ports-info strong {
            color: #0284c7;
        }
        
        .port-item {
            margin: 8px 0;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 1.8em;
            }
            
            .button-group {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AyazDy</h1>
            <p class="subtitle">Task Queue Control Center</p>
        </div>
        
        <div class="info-box">
            <strong>📋 Select a project and trigger task queue execution</strong><br>
            Tasks will run in sequence. You can monitor progress below.
        </div>
        
        <div class="form-group">
            <label for="project">🔷 Choose Project:</label>
            <select id="project" onchange="updateTasks()">
                <option value="default">Loading projects...</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="tasks">📌 Queued Tasks:</label>
            <select id="tasks" multiple size="6">
                <option>No tasks queued</option>
            </select>
            <small style="color: #666; margin-top: 8px; display: block;">
                ℹ️ Tasks will execute in alphabetical order (01-, 02-, 03-, etc.)
            </small>
        </div>
        
        <div class="form-group">
            <label for="limit">⏱️ Max Tasks to Run (Optional):</label>
            <input type="number" id="limit" min="1" placeholder="Leave empty to run all queued tasks">
        </div>
        
        <div class="button-group">
            <button class="btn-trigger" onclick="triggerQueue()">
                ▶️ Trigger Queue
            </button>
            <button class="btn-status" onclick="checkStatus()">
                🔄 Refresh Status
            </button>
        </div>
        
        <div id="status" class="status-box">
            <h3 style="margin-bottom: 20px;">📊 Execution Status</h3>
            <div id="status-content"></div>
        </div>
        
        <div class="ports-info">
            <strong>🌐 Access Points:</strong><br>
            <div class="port-item">
                <strong>Dashboard:</strong> http://localhost:9890 (this page)
            </div>
            <div class="port-item">
                <strong>REST API:</strong> http://localhost:9234
            </div>
            <div class="port-item">
                <strong>Grafana:</strong> http://localhost:9543
            </div>
            <div class="port-item">
                <strong>Prometheus:</strong> http://localhost:9654
            </div>
        </div>
    </div>
    
    <script>
        const API_URL = "http://localhost:9234";
        
        // Load projects on page load
        window.onload = function() {
            loadProjects();
            setInterval(checkStatus, 5000); // Auto-refresh every 5 seconds
        };
        
        async function loadProjects() {
            try {
                const response = await fetch(`${API_URL}/api/queue/status`);
                const data = await response.json();
                
                const projectSelect = document.getElementById('project');
                projectSelect.innerHTML = `<option value="default">Default Project</option>`;
                
                // Get projects from queue structure
                updateTasks();
            } catch (error) {
                console.error('Error loading projects:', error);
                showError('Failed to load projects. Is the API running?');
            }
        }
        
        async function updateTasks() {
            try {
                const response = await fetch(`${API_URL}/api/queue/status`);
                const data = await response.json();
                
                const tasksSelect = document.getElementById('tasks');
                const queue = data.queue || [];
                
                if (queue.length === 0) {
                    tasksSelect.innerHTML = '<option>No tasks in queue</option>';
                } else {
                    tasksSelect.innerHTML = queue.map(task => 
                        `<option selected>${task}</option>`
                    ).join('');
                }
            } catch (error) {
                console.error('Error loading tasks:', error);
            }
        }
        
        async function triggerQueue() {
            const project = document.getElementById('project').value;
            const limit = document.getElementById('limit').value;
            
            const statusDiv = document.getElementById('status');
            const statusContent = document.getElementById('status-content');
            
            statusContent.innerHTML = '<div><span class="spinner"></span> Triggering queue...</div>';
            statusDiv.classList.add('show');
            
            try {
                const params = new URLSearchParams();
                if (limit) params.append('limit', limit);
                params.append('timeout', '600');
                
                const response = await fetch(`${API_URL}/api/queue/run?${params}`, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const results = await response.json();
                
                let html = `<div class="status-item">
                    <div class="status-label">✅ Executed</div>
                    <div class="status-value success">${results.length} task(s) completed</div>
                </div>`;
                
                results.forEach((task, index) => {
                    const icon = task.status === 'executed' ? '✅' : 
                                task.status === 'failed' ? '❌' : '⏭️';
                    html += `<div class="status-item">
                        <div>${icon} ${task.name}</div>
                        <div style="font-size: 0.9em; color: #666;">Status: ${task.status}</div>
                    </div>`;
                });
                
                statusContent.innerHTML = html;
                updateTasks();
                
            } catch (error) {
                console.error('Error triggering queue:', error);
                statusContent.innerHTML = `<div class="status-item">
                    <div class="status-label">❌ Error</div>
                    <div class="status-value error">${error.message}</div>
                </div>`;
            }
        }
        
        async function checkStatus() {
            try {
                const response = await fetch(`${API_URL}/api/queue/status`);
                const data = await response.json();
                
                const statusDiv = document.getElementById('status');
                const statusContent = document.getElementById('status-content');
                
                let html = `
                    <div class="status-item">
                        <div class="status-label">📋 Queued Tasks</div>
                        <div class="status-value">${data.queue.length}</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">✅ Completed Tasks</div>
                        <div class="status-value success">${data.completed.length}</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">🔄 Deferred Tasks</div>
                        <div class="status-value warning">${data.later.length}</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">📊 Success Rate</div>
                        <div class="status-value">${data.success_rate.toFixed(1)}%</div>
                    </div>
                `;
                
                statusContent.innerHTML = html;
                statusDiv.classList.add('show');
            } catch (error) {
                console.error('Error checking status:', error);
            }
        }
        
        function showError(message) {
            const statusDiv = document.getElementById('status');
            const statusContent = document.getElementById('status-content');
            statusContent.innerHTML = `<div class="status-item">
                <div class="status-label">⚠️ Warning</div>
                <div class="status-value error">${message}</div>
            </div>`;
            statusDiv.classList.add('show');
        }
    </script>
</body>
</html>
    """)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "ayazdy-dashboard", "port": DASHBOARD_PORT}

@app.post("/api/trigger-queue")
async def trigger_queue(project: str = "default", limit: int = None):
    """Trigger queue execution via API"""
    try:
        async with aiohttp.ClientSession() as session:
            params = {"timeout": 600}
            if limit:
                params["limit"] = limit
            
            async with session.post(f"{API_URL}/api/queue/run", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise HTTPException(status_code=resp.status, detail="API Error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def get_projects_list():
    """Get list of available projects"""
    return {"projects": get_projects()}

@app.get("/api/projects/{project}/tasks")
async def get_tasks(project: str):
    """Get tasks for a specific project"""
    return {"project": project, "tasks": get_project_tasks(project)}

@app.get("/api/queue/status")
async def get_queue_status():
    """Get queue status from API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/queue/status") as resp:
                return await resp.json()
    except Exception as e:
        return {"error": str(e), "queue": [], "completed": [], "later": [], "success_rate": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=DASHBOARD_PORT)
