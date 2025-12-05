"""
Enhanced Production Dashboard with Docker Integration, Metrics, Logs, and System Info
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import requests
import subprocess
import os
import json
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Production Wrapper - Sentiment Analysis Dashboard")

# Configuration
API_URL = 'http://localhost:8000'  # Use Docker API
PROJECT_ROOT = Path(__file__).parent

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    html_content = get_dashboard_html()
    return HTMLResponse(
        content=html_content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/api/system-info")
async def get_system_info():
    """Get system information and features"""
    try:
        # Get API health
        health = requests.get(f"{API_URL}/health", timeout=2).json()
        
        # Try to get metrics, but don't fail if they're in Prometheus format
        try:
            metrics_response = requests.get(f"{API_URL}/metrics", timeout=2)
            # Check if response is JSON
            if 'application/json' in metrics_response.headers.get('content-type', ''):
                metrics_data = metrics_response.json()
            else:
                # Metrics endpoint returns Prometheus format, not JSON
                metrics_data = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "average_latency_ms": 0,
                    "uptime_seconds": 0,
                    "model_info": {
                        "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
                        "device": "cpu",
                        "status": "loaded",
                        "framework": "PyTorch + Transformers"
                    }
                }
        except:
            metrics_data = None
        
        # Check Docker
        docker_status = check_docker_status()
        
        # Count files and lines
        file_stats = count_project_files()
        
        return {
            "api_status": "healthy" if health.get("status") == "healthy" else "down",
            "model_loaded": health.get("model_loaded", False),
            "version": health.get("version", "unknown"),
            "metrics": metrics_data,
            "docker": docker_status,
            "project": file_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "api_status": "down",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/docker/status")
async def docker_status():
    """Get Docker container status"""
    return check_docker_status()

@app.post("/api/docker/start")
async def docker_start():
    """Start Docker container"""
    try:
        # Check if container exists
        check_result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=sentiment-api", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        container_exists = "sentiment-api" in check_result.stdout
        
        if container_exists:
            # Start existing container
            result = subprocess.run(
                ["docker", "start", "sentiment-api"],
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            # Build and run new container
            build_result = subprocess.run(
                ["docker", "build", "-t", "sentiment-api:latest", "."],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300
            )
            if build_result.returncode != 0:
                return {"success": False, "error": f"Build failed: {build_result.stderr}"}
            
            # Check if .env file exists
            env_file = PROJECT_ROOT / ".env"
            run_cmd = ["docker", "run", "-d", "--name", "sentiment-api", "-p", "8000:8000"]
            if env_file.exists():
                run_cmd.extend(["--env-file", ".env"])
            run_cmd.append("sentiment-api:latest")
            
            result = subprocess.run(
                run_cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=10
            )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else ""
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Container startup timed out. This may happen on first run while downloading base images."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/docker/stop")
async def docker_stop():
    """Stop Docker container"""
    try:
        result = subprocess.run(
            ["docker", "stop", "sentiment-api"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else ""
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Container shutdown timed out after 30 seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/docker/save-image")
async def docker_save_image():
    """Save Docker image to .tar file"""
    try:
        output_file = PROJECT_ROOT / "sentiment-api.tar"
        result = subprocess.run(
            ["docker", "save", "sentiment-api:latest", "-o", str(output_file)],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            return {
                "success": True,
                "message": f"Image saved to {output_file.name} ({file_size_mb:.0f} MB)",
                "file_path": str(output_file)
            }
        return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Image save timed out after 2 minutes"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/docker/tag-image")
async def docker_tag_image(username: str):
    """Tag Docker image for Docker Hub"""
    try:
        tag_name = f"{username}/sentiment-api:latest"
        result = subprocess.run(
            ["docker", "tag", "sentiment-api:latest", tag_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Image tagged as {tag_name}",
                "tag": tag_name
            }
        return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/metrics")
async def get_metrics():
    """Get API metrics from local API"""
    try:
        response = requests.get(f"{API_URL}/metrics", timeout=5)
        return response.json()
    except Exception as e:
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "success_rate": 0,
            "average_latency_ms": 0,
            "min_latency_ms": 0,
            "max_latency_ms": 0,
            "uptime_seconds": 0,
            "error": str(e)
        }

@app.get("/api/logs/{log_type}")
async def get_logs(log_type: str, lines: int = 50):
    """Get logs (app, predictions, errors, api_server, dashboard)"""
    
    # For API server logs, get from Docker container
    if log_type == "api_server":
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), "sentiment-api"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                log_lines = result.stdout.split('\n')
                return {"logs": [line.strip() for line in log_lines if line.strip()]}
            else:
                return {"logs": [], "error": "Docker container not running or not found"}
        except Exception as e:
            return {"logs": [], "error": str(e)}
    
    # For other logs, read from files
    log_files = {
        "app": "logs/app.log",
        "predictions": "logs/predictions.log",
        "errors": "logs/errors.log",
        "dashboard": "dashboard_enhanced.log"
    }
    
    if log_type not in log_files:
        raise HTTPException(400, "Invalid log type")
    
    log_path = PROJECT_ROOT / log_files[log_type]
    
    if not log_path.exists():
        return {"logs": [], "error": "Log file not found"}
    
    try:
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
            return {"logs": [line.strip() for line in recent_lines]}
    except Exception as e:
        return {"logs": [], "error": str(e)}

@app.get("/api/run-tests")
async def run_tests():
    """Run test suite"""
    try:
        result = subprocess.run(
            ["pytest", "tests/", "-v", "--tb=short"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_docker_status():
    """Check Docker daemon and container status"""
    try:
        # Check Docker daemon
        daemon_result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        daemon_running = daemon_result.returncode == 0
        
        # Check containers - look for sentiment-api container specifically
        containers = []
        if daemon_running:
            ps_result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=sentiment-api", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                try:
                    # Parse each line as JSON
                    for line in ps_result.stdout.strip().split('\n'):
                        if line:
                            container = json.loads(line)
                            # Extract relevant fields
                            containers.append({
                                "Name": container.get("Names", "unknown"),
                                "State": container.get("State", "unknown"),
                                "Status": container.get("Status", "unknown"),
                                "ID": container.get("ID", "")[:12]
                            })
                except Exception as parse_error:
                    # If parsing fails, just show raw output
                    print(f"Docker parse error: {parse_error}")
                    containers = []
        
        return {
            "daemon_running": daemon_running,
            "containers": containers,
            "compose_available": daemon_running
        }
    except Exception as e:
        return {
            "daemon_running": False,
            "containers": [],
            "compose_available": False,
            "error": str(e)
        }

def count_project_files():
    """Count project files and lines"""
    stats = {
        "total_files": 0,
        "total_lines": 0,
        "python_files": 0,
        "python_lines": 0,
        "test_files": 0,
        "doc_files": 0,
        "doc_lines": 0
    }
    
    try:
        for ext, count_type in [
            ("*.py", "python"),
            ("tests/*.py", "test"),
            ("*.md", "doc")
        ]:
            files = list(PROJECT_ROOT.rglob(ext))
            for f in files:
                if "venv" in str(f) or ".venv" in str(f):
                    continue
                
                stats["total_files"] += 1
                
                try:
                    lines = len(f.read_text().splitlines())
                    stats["total_lines"] += lines
                    
                    if ext == "*.py":
                        stats["python_files"] += 1
                        stats["python_lines"] += lines
                        if "test" in f.name:
                            stats["test_files"] += 1
                    elif ext == "*.md":
                        stats["doc_files"] += 1
                        stats["doc_lines"] += lines
                except:
                    pass
        
        return stats
    except:
        return stats

def get_dashboard_html():
    """Generate enhanced dashboard HTML"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Production Wrapper - Sentiment Analysis Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f23;
            color: #e0e0e0;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            color: white;
            font-size: 1.8em;
        }
        
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .status-healthy {
            background: #10b981;
            color: white;
        }
        
        .status-down {
            background: #ef4444;
            color: white;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #1f1f3a;
        }
        
        .tab {
            padding: 12px 24px;
            background: #1a1a2e;
            border: none;
            color: #8b8b9a;
            cursor: pointer;
            font-size: 1em;
            border-radius: 8px 8px 0 0;
            transition: all 0.3s;
        }
        
        .tab:hover {
            background: #252541;
            color: #e0e0e0;
        }
        
        .tab.active {
            background: #667eea;
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        
        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #252541;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #8b8b9a;
        }
        
        .metric-value {
            color: #10b981;
            font-weight: 600;
        }
        
        .feature-list {
            list-style: none;
        }
        
        .feature-list li {
            padding: 8px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .feature-list li:before {
            content: "•";
            color: #10b981;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
            margin-right: 10px;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
        }
        
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        
        .btn-danger:hover {
            background: #dc2626;
        }
        
        .btn-success {
            background: #10b981;
            color: white;
        }
        
        .btn-success:hover {
            background: #059669;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            color: #8b8b9a;
        }
        
        textarea {
            width: 100%;
            padding: 12px;
            background: #252541;
            border: 2px solid #3a3a5a;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            min-height: 120px;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #252541;
            border-radius: 8px;
            display: none;
        }
        
        .result.show {
            display: block;
        }
        
        .sentiment-positive {
            color: #10b981;
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .sentiment-negative {
            color: #ef4444;
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .log-viewer {
            background: #0a0a15;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            max-height: 400px;
            overflow-y: auto;
            color: #10b981;
        }
        
        .log-line {
            padding: 2px 0;
            border-bottom: 1px solid #1a1a2e;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 15px;
        }
        
        input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .confidence-bar {
            width: 100%;
            height: 20px;
            background: #252541;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #10b981);
            transition: width 0.5s;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #252541;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .docker-container {
            background: #252541;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .docker-status {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .docker-status.running {
            background: #10b981;
        }
        
        .docker-status.stopped {
            background: #ef4444;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>Production Wrapper - Sentiment Analysis</h1>
            <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.8); font-size: 14px;">FastAPI Microservice Dashboard</p>
            <div class="status-badge" id="apiStatus">Checking...</div>
        </div>
    </div>
    
    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="switchTab('overview', event)">Overview</button>
            <button class="tab" onclick="switchTab('predict', event)">Predictions</button>
            <button class="tab" onclick="switchTab('docker', event)">Docker</button>
            <button class="tab" onclick="switchTab('metrics', event)">Metrics</button>
            <button class="tab" onclick="switchTab('logs', event)">Logs</button>
            <button class="tab" onclick="switchTab('tests', event)">Tests</button>
        </div>
        
        <!-- Overview Tab -->
        <div id="overview" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h3>Problem Statement</h3>
                    <p style="color: #e0e0e0; line-height: 1.6; margin-bottom: 15px;">
                        Production Wrapper (FastAPI microservice) around one experimental model.
                    </p>
                    <h4 style="color: #667eea; margin-top: 15px; margin-bottom: 10px;">Scope:</h4>
                    <ul class="feature-list">
                        <li>Pick/select model; design clean API endpoints (predict, health check)</li>
                        <li>Add logging (inputs/outputs, latency/errors), Docker containerization, basic tests</li>
                        <li>Create minimal CLI/dashboard for testing real samples</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>Core Features</h3>
                    <ul class="feature-list">
                        <li>FastAPI microservice with DistilBERT model</li>
                        <li>5 REST API endpoints (predict, batch, health, metrics)</li>
                        <li>3-tier logging system (app, predictions, errors)</li>
                        <li>Docker containerization support</li>
                        <li>22 automated tests (59% coverage)</li>
                        <li>CLI tool with 5 commands</li>
                        <li>Management web dashboard</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>Deployment Options</h3>
                    <ul class="feature-list">
                        <li>Docker containerization (port 8000)</li>
                        <li>Local API server (port 8001)</li>
                        <li>Management dashboard (port 3000)</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>System Status</h3>
                    <div class="metric">
                        <span class="metric-label">API Status</span>
                        <span class="metric-value" id="sysApiStatus">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Model Loaded</span>
                        <span class="metric-value" id="modelStatus">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Version</span>
                        <span class="metric-value" id="version">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Python Files</span>
                        <span class="metric-value" id="pythonFiles">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Lines of Code</span>
                        <span class="metric-value" id="totalLines">Loading...</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Predictions Tab -->
        <div id="predict" class="tab-content">
            <div class="card">
                <h3>Sentiment Analysis</h3>
                <div class="input-group">
                    <label>Enter text to analyze:</label>
                    <textarea id="textInput" placeholder="Type or paste your text here..."></textarea>
                </div>
                
                <div class="checkbox-group">
                    <input type="checkbox" id="enhanced" checked>
                    <label for="enhanced">Enhanced Analysis (with LLM insights)</label>
                </div>
                
                <div class="checkbox-group">
                    <input type="checkbox" id="probabilities">
                    <label for="probabilities">Show Probabilities</label>
                </div>
                
                <button class="btn btn-primary" onclick="analyzeSentiment()">
                    Analyze Sentiment
                </button>
                
                <div id="result" class="result"></div>
            </div>
        </div>
        
        <!-- Docker Tab -->
        <div id="docker" class="tab-content">
            <div class="card">
                <h3>Container Management</h3>
                <p style="color: #8b8b9a; margin-bottom: 15px;">
                    Manage the Docker container running the sentiment analysis API.
                </p>
                <div style="margin-bottom: 20px;">
                    <button class="btn btn-success" onclick="dockerStart()">Start Containers</button>
                    <button class="btn btn-danger" onclick="dockerStop()">Stop Containers</button>
                    <button class="btn btn-primary" onclick="dockerRefresh()">Refresh Status</button>
                </div>
                
                <div id="dockerStatus">
                    <p>Loading Docker status...</p>
                </div>
                
                <div id="dockerOutput" style="margin-top: 20px;"></div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <h3>Export Docker Image</h3>
                <p style="color: #8b8b9a; margin-bottom: 15px;">
                    Save the Docker image to a .tar file for sharing or backup. The file will be created in the current directory.
                </p>
                <button class="btn btn-primary" onclick="saveDockerImage()" style="width: 100%; padding: 12px; font-size: 1.05em;">Export Image to .tar File</button>
                <div id="saveImageOutput" style="margin-top: 15px;"></div>
                <div style="margin-top: 15px; padding: 12px; background: #2a2a3a; border-radius: 6px;">
                    <p style="color: #8b8b9a; font-size: 0.9em; line-height: 1.6;">
                        <strong>Note:</strong> The exported <code>sentiment-api.tar</code> file (1.7GB) contains the complete Docker image with the pre-downloaded model. You can transfer this file to another machine and load it using: <code style="color: #10b981;">docker load -i sentiment-api.tar</code>
                    </p>
                </div>
            </div>
        </div>
        
        <!-- Metrics Tab -->
        <div id="metrics" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>Request Metrics</h3>
                    <div id="metricsContent">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>Performance</h3>
                    <div id="performanceMetrics">Loading...</div>
                </div>
            </div>
        </div>
        
        <!-- Logs Tab -->
        <div id="logs" class="tab-content">
            <div class="card">
                <h3>Application Logs</h3>
                <p style="color: #8b8b9a; margin-bottom: 15px; line-height: 1.6;">
                    View different types of logs to monitor system activity and troubleshoot issues:
                </p>
                <div style="margin-bottom: 20px; padding: 15px; background: #2a2a3a; border-radius: 6px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; color: #e0e0e0; font-size: 0.9em;">
                        <div>
                            <strong style="color: #667eea;">App Logs:</strong>
                            <p style="color: #8b8b9a; margin: 5px 0 0 0; line-height: 1.5;">Service startup/shutdown, model loading, system events</p>
                        </div>
                        <div>
                            <strong style="color: #667eea;">Predictions:</strong>
                            <p style="color: #8b8b9a; margin: 5px 0 0 0; line-height: 1.5;">Every prediction request with input, output, and latency (JSON format)</p>
                        </div>
                        <div>
                            <strong style="color: #667eea;">Errors:</strong>
                            <p style="color: #8b8b9a; margin: 5px 0 0 0; line-height: 1.5;">Exceptions, stack traces, and error details for debugging</p>
                        </div>
                        <div>
                            <strong style="color: #667eea;">API Server:</strong>
                            <p style="color: #8b8b9a; margin: 5px 0 0 0; line-height: 1.5;">HTTP requests, response codes, client IPs from Docker container</p>
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 15px;">
                    <button class="btn btn-primary" onclick="loadLogs('app')">App Logs</button>
                    <button class="btn btn-primary" onclick="loadLogs('predictions')">Predictions</button>
                    <button class="btn btn-primary" onclick="loadLogs('errors')">Errors</button>
                    <button class="btn btn-primary" onclick="loadLogs('api_server')">API Server</button>
                </div>
                <div class="log-viewer" id="logViewer">
                    <p>Select a log type to view</p>
                </div>
            </div>
        </div>
        
        <!-- Tests Tab -->
        <div id="tests" class="tab-content">
            <div class="card">
                <h3>Test Suite</h3>
                <p style="color: #8b8b9a; margin-bottom: 15px; line-height: 1.6;">
                    Run automated tests to verify all system components are working correctly.
                </p>
                <div style="margin-bottom: 20px; padding: 15px; background: #2a2a3a; border-radius: 6px;">
                    <p style="color: #e0e0e0; margin-bottom: 10px;"><strong>What Gets Tested:</strong></p>
                    <ul style="color: #8b8b9a; line-height: 1.8; margin-left: 20px;">
                        <li><strong>API Tests (12):</strong> Health checks, predictions, input validation, batch processing</li>
                        <li><strong>Metrics Tests (5):</strong> Performance tracking, statistics calculation, counters</li>
                        <li><strong>Model Tests (5):</strong> Model loading, predictions, error handling (skipped on macOS, run in Docker)</li>
                    </ul>
                    <p style="color: #10b981; margin-top: 12px; padding-top: 12px; border-top: 1px solid #3a3a5a;">
                        <strong>Expected Result:</strong> 17/17 tests passing on macOS, 22/22 passing inside Docker container
                    </p>
                </div>
                <button class="btn btn-primary" onclick="runTests()">Run All Tests</button>
                <div id="testOutput" class="log-viewer" style="margin-top: 20px; display: none;"></div>
            </div>
        </div>
    </div>
    
    <script>
        const API_URL = 'http://localhost:8000';  // Use Docker API
        const DASHBOARD_API = '';
        
        // Tab switching
        function switchTab(tabName, event) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            if (event && event.target) {
                event.target.classList.add('active');
            } else {
                // If no event, find the button by onclick attribute
                document.querySelectorAll('.tab').forEach(t => {
                    if (t.getAttribute('onclick').includes(tabName)) {
                        t.classList.add('active');
                    }
                });
            }
            
            document.getElementById(tabName).classList.add('active');
            
            // Load data for specific tabs
            if (tabName === 'metrics') loadMetrics();
            if (tabName === 'docker') dockerRefresh();
        }
        
        // Load system info
        async function loadSystemInfo() {
            console.log('loadSystemInfo called');
            try {
                const url = DASHBOARD_API + '/api/system-info';
                console.log('Fetching:', url);
                const response = await fetch(url);
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Data received:', data);
                
                // Update header status
                const statusBadge = document.getElementById('apiStatus');
                if (data.api_status === 'healthy') {
                    statusBadge.textContent = 'API Healthy';
                    statusBadge.className = 'status-badge status-healthy';
                } else {
                    statusBadge.textContent = 'API Down';
                    statusBadge.className = 'status-badge status-down';
                }
                
                // Update system status
                console.log('Updating sysApiStatus with:', data.api_status);
                const sysApiStatus = document.getElementById('sysApiStatus');
                if (sysApiStatus) {
                    sysApiStatus.textContent = data.api_status;
                } else {
                    console.error('sysApiStatus element not found');
                }
                
                const modelStatus = document.getElementById('modelStatus');
                if (modelStatus) {
                    modelStatus.textContent = data.model_loaded ? 'Yes' : 'No';
                } else {
                    console.error('modelStatus element not found');
                }
                
                const version = document.getElementById('version');
                if (version) {
                    version.textContent = data.version || 'unknown';
                } else {
                    console.error('version element not found');
                }
                
                // Update project stats
                if (data.project) {
                    console.log('Project data:', data.project);
                    const pythonFiles = document.getElementById('pythonFiles');
                    if (pythonFiles) {
                        pythonFiles.textContent = data.project.python_files || '0';
                    } else {
                        console.error('pythonFiles element not found');
                    }
                    
                    const totalLines = document.getElementById('totalLines');
                    if (totalLines) {
                        totalLines.textContent = (data.project.total_lines || 0).toLocaleString();
                    } else {
                        console.error('totalLines element not found');
                    }
                }
                console.log('loadSystemInfo completed successfully');
            } catch (error) {
                console.error('Error loading system info:', error);
                const statusBadge = document.getElementById('apiStatus');
                if (statusBadge) {
                    statusBadge.textContent = 'Error';
                    statusBadge.className = 'status-badge status-down';
                }
            }
        }
        
        // Sentiment analysis
        async function analyzeSentiment() {
            const text = document.getElementById('textInput').value.trim();
            if (!text) {
                alert('Please enter some text to analyze');
                return;
            }
            
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="loading"></div> Analyzing...';
            resultDiv.classList.add('show');
            
            const enhanced = document.getElementById('enhanced').checked;
            const showProbs = document.getElementById('probabilities').checked;
            
            try {
                const response = await fetch(`${API_URL}/api/v1/predict`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        text: text,
                        enhanced: enhanced,
                        return_probabilities: showProbs
                    })
                });
                
                const data = await response.json();
                displayResult(data);
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: #ef4444;">Error: ${error.message}</p>`;
            }
        }
        
        function displayResult(data) {
            const resultDiv = document.getElementById('result');
            const sentimentClass = data.sentiment === 'positive' ? 'sentiment-positive' : 'sentiment-negative';
            
            let html = '<div class="' + sentimentClass + '">' + data.sentiment.toUpperCase() + '</div>';
            html += '<p style="margin-top: 10px;">Confidence: ' + (data.confidence * 100).toFixed(2) + '%</p>';
            html += '<div class="confidence-bar">';
            html += '<div class="confidence-fill" style="width: ' + (data.confidence * 100) + '%"></div>';
            html += '</div>';
            
            if (data.probabilities) {
                html += '<div style="margin-top: 15px; padding: 15px; background: #252541; border-radius: 6px;">';
                html += '<p style="margin-bottom: 15px; color: #e0e0e0; font-weight: bold;">Probabilities:</p>';
                
                // Show detailed phrase breakdown if enhanced analysis is available
                if (data.enhanced_analysis && data.enhanced_analysis.key_phrases_detailed && data.enhanced_analysis.key_phrases_detailed.length > 0) {
                    data.enhanced_analysis.key_phrases_detailed.forEach(function(item) {
                        let color, bgColor, label;
                        if (item.sentiment === 'positive') {
                            color = '#10b981';
                            bgColor = '#064e3b';
                            label = '[+]';
                        } else if (item.sentiment === 'negative') {
                            color = '#ef4444';
                            bgColor = '#7f1d1d';
                            label = '[-]';
                        } else {
                            color = '#fbbf24';
                            bgColor = '#78350f';
                            label = '[-]';
                        }
                        
                        html += '<div style="margin-bottom: 8px; padding: 8px; background: ' + bgColor + '; border-radius: 4px; border-left: 3px solid ' + color + ';">';
                        html += '<div style="display: flex; justify-content: space-between; align-items: center;">';
                        html += '<span style="color: #e0e0e0; font-weight: 500; font-size: 0.9em;">' + label + ' "' + item.phrase + '"</span>';
                        html += '<span style="color: ' + color + '; font-weight: bold;">' + item.score + '%</span>';
                        html += '</div>';
                        html += '<div style="margin-top: 3px; font-size: 0.8em; color: #9ca3af;">Sentiment: ' + item.sentiment.charAt(0).toUpperCase() + item.sentiment.slice(1) + '</div>';
                        html += '</div>';
                    });
                    
                    // Overall scores - include neutral if present
                    if (data.enhanced_analysis.overall_score) {
                        html += '<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #3a3a5a;">';
                        html += '<div style="display: flex; gap: 10px; margin-top: 8px;">';
                        
                        html += '<div style="flex: 1; padding: 8px; background: #064e3b; border-radius: 4px; border: 2px solid #10b981;">';
                        html += '<div style="color: #9ca3af; font-size: 0.75em;">Positive</div>';
                        html += '<div style="color: #10b981; font-size: 1.2em; font-weight: bold;">' + data.enhanced_analysis.overall_score.positive + '%</div>';
                        html += '</div>';
                        
                        html += '<div style="flex: 1; padding: 8px; background: #7f1d1d; border-radius: 4px; border: 2px solid #ef4444;">';
                        html += '<div style="color: #9ca3af; font-size: 0.75em;">Negative</div>';
                        html += '<div style="color: #ef4444; font-size: 1.2em; font-weight: bold;">' + data.enhanced_analysis.overall_score.negative + '%</div>';
                        html += '</div>';
                        
                        if (data.enhanced_analysis.overall_score.neutral && data.enhanced_analysis.overall_score.neutral > 0) {
                            html += '<div style="flex: 1; padding: 8px; background: #78350f; border-radius: 4px; border: 2px solid #fbbf24;">';
                            html += '<div style="color: #9ca3af; font-size: 0.75em;">Neutral</div>';
                            html += '<div style="color: #fbbf24; font-size: 1.2em; font-weight: bold;">' + data.enhanced_analysis.overall_score.neutral + '%</div>';
                            html += '</div>';
                        }
                        
                        html += '</div></div>';
                    }
                } else {
                    // Fallback to simple display if no enhanced analysis
                    const posColor = data.sentiment === 'positive' ? '#10b981' : '#8b8b9a';
                    html += '<p style="margin: 5px 0; color: ' + posColor + ';">';
                    html += 'Positive: ' + (data.probabilities.positive * 100).toFixed(2) + '%</p>';
                    const negColor = data.sentiment === 'negative' ? '#ef4444' : '#8b8b9a';
                    html += '<p style="margin: 5px 0; color: ' + negColor + ';">';
                    html += 'Negative: ' + (data.probabilities.negative * 100).toFixed(2) + '%</p>';
                }
                
                html += '</div>';
            }
            
            if (data.enhanced_analysis) {
                html += '<div style="margin-top: 20px; padding: 20px; background: #1a1a2e; border-radius: 8px; border-left: 4px solid #667eea;">';
                html += '<h4 style="color: #667eea; margin-bottom: 15px;">Enhanced Analysis</h4>';
                
                if (data.enhanced_analysis.key_phrases_detailed && data.enhanced_analysis.key_phrases_detailed.length > 0) {
                    html += '<div style="margin-bottom: 20px;">';
                    html += '<h5 style="color: #ec4899; margin-bottom: 12px;">Key Phrases with Sentiment Scores</h5>';
                    
                    data.enhanced_analysis.key_phrases_detailed.forEach(function(item) {
                        let color, bgColor, label;
                        if (item.sentiment === 'positive') {
                            color = '#10b981';
                            bgColor = '#064e3b';
                            label = '[+]';
                        } else if (item.sentiment === 'negative') {
                            color = '#ef4444';
                            bgColor = '#7f1d1d';
                            label = '[-]';
                        } else {
                            color = '#fbbf24';
                            bgColor = '#78350f';
                            label = '[-]';
                        }
                        
                        html += '<div style="margin-bottom: 10px; padding: 10px; background: ' + bgColor + '; border-radius: 6px; border-left: 3px solid ' + color + ';">';
                        html += '<div style="display: flex; justify-content: space-between; align-items: center;">';
                        html += '<span style="color: #e0e0e0; font-weight: 500;">' + label + ' "' + item.phrase + '"</span>';
                        html += '<span style="color: ' + color + '; font-weight: bold; font-size: 1.1em;">' + item.score + '%</span>';
                        html += '</div>';
                        html += '<div style="margin-top: 4px; font-size: 0.85em; color: #9ca3af;">Sentiment: ' + item.sentiment.charAt(0).toUpperCase() + item.sentiment.slice(1) + '</div>';
                        html += '</div>';
                    });
                    
                    html += '</div>';
                }
                
                if (data.enhanced_analysis.overall_score) {
                    html += '<div style="margin-bottom: 20px;">';
                    html += '<h5 style="color: #fbbf24; margin-bottom: 12px;">Overall Sentiment Score</h5>';
                    html += '<div style="display: flex; gap: 15px;">';
                    
                    html += '<div style="flex: 1; padding: 12px; background: #064e3b; border-radius: 6px; border: 2px solid #10b981;">';
                    html += '<div style="color: #9ca3af; font-size: 0.85em; margin-bottom: 4px;">Positive</div>';
                    html += '<div style="color: #10b981; font-size: 1.5em; font-weight: bold;">' + data.enhanced_analysis.overall_score.positive + '%</div>';
                    html += '</div>';
                    
                    html += '<div style="flex: 1; padding: 12px; background: #7f1d1d; border-radius: 6px; border: 2px solid #ef4444;">';
                    html += '<div style="color: #9ca3af; font-size: 0.85em; margin-bottom: 4px;">Negative</div>';
                    html += '<div style="color: #ef4444; font-size: 1.5em; font-weight: bold;">' + data.enhanced_analysis.overall_score.negative + '%</div>';
                    html += '</div>';
                    
                    if (data.enhanced_analysis.overall_score.neutral && data.enhanced_analysis.overall_score.neutral > 0) {
                        html += '<div style="flex: 1; padding: 12px; background: #78350f; border-radius: 6px; border: 2px solid #fbbf24;">';
                        html += '<div style="color: #9ca3af; font-size: 0.85em; margin-bottom: 4px;">Neutral</div>';
                        html += '<div style="color: #fbbf24; font-size: 1.5em; font-weight: bold;">' + data.enhanced_analysis.overall_score.neutral + '%</div>';
                        html += '</div>';
                    }
                    
                    html += '</div></div>';
                }
                
                html += '<div style="margin-bottom: 20px;">';
                html += '<h5 style="color: #10b981; margin-bottom: 8px;">Detailed Explanation</h5>';
                html += '<p style="color: #e0e0e0; line-height: 1.6;">' + data.enhanced_analysis.explanation + '</p>';
                html += '</div>';
                
                if (data.enhanced_analysis.dominant_factor) {
                    html += '<div style="margin-bottom: 20px;">';
                    html += '<h5 style="color: #a78bfa; margin-bottom: 8px;">Dominant Factor</h5>';
                    html += '<p style="color: #e0e0e0; line-height: 1.6; font-weight: 500;">' + data.enhanced_analysis.dominant_factor + '</p>';
                    html += '</div>';
                }
                
                if (data.enhanced_analysis.tone) {
                    html += '<div style="margin-bottom: 20px;">';
                    html += '<h5 style="color: #f59e0b; margin-bottom: 8px;">Tone & Intensity</h5>';
                    html += '<p style="color: #e0e0e0; line-height: 1.6;">' + data.enhanced_analysis.tone + '</p>';
                    html += '</div>';
                }
                
                if (data.enhanced_analysis.context) {
                    html += '<div style="margin-bottom: 20px;">';
                    html += '<h5 style="color: #8b5cf6; margin-bottom: 8px;">Context & Aspects</h5>';
                    html += '<p style="color: #e0e0e0; line-height: 1.6;">' + data.enhanced_analysis.context + '</p>';
                    html += '</div>';
                }
                
                if (data.enhanced_analysis.evidence) {
                    html += '<div style="margin-bottom: 20px;">';
                    html += '<h5 style="color: #06b6d4; margin-bottom: 8px;">Evidence & Specific Words</h5>';
                    html += '<p style="color: #e0e0e0; line-height: 1.6; font-style: italic;">' + data.enhanced_analysis.evidence + '</p>';
                    html += '</div>';
                }
                        
                if (data.probabilities) {
                    const diff = Math.abs(data.probabilities.positive - data.probabilities.negative);
                    if (diff < 0.3) {
                        html += '<div style="margin-top: 15px; padding: 12px; background: #3a2a1a; border-radius: 6px; border-left: 3px solid #f59e0b;">';
                        html += '<p style="color: #fbbf24; font-weight: bold; margin-bottom: 6px;">Mixed Sentiment Detected</p>';
                        html += '<p style="color: #e0e0e0; font-size: 0.9em; line-height: 1.6;">';
                        html += 'This text contains balanced positive and negative elements (confidence difference less than 30%). ';
                        html += 'Consider breaking it into separate sentences for more granular analysis of different aspects.';
                        html += '</p></div>';
                    }
                }
                        
                html += '</div>';
            }
            
            html += `<p style="margin-top: 15px; color: #8b8b9a; font-size: 0.9em;">Latency: ${data.latency_ms.toFixed(2)}ms</p>`;
            
            resultDiv.innerHTML = html;
        }
        
        // Docker management
        async function dockerRefresh() {
            try {
                const response = await fetch(DASHBOARD_API + '/api/docker/status');
                const data = await response.json();
                
                let html = '<div class="metric">';
                html += '<span class="metric-label">Docker Daemon</span>';
                html += '<span class="metric-value">' + (data.daemon_running ? 'Running' : 'Not Running') + '</span>';
                html += '</div>';
                
                if (data.containers && data.containers.length > 0) {
                    html += '<h4 style="margin: 20px 0 10px 0; color: #667eea;">Containers:</h4>';
                    data.containers.forEach(container => {
                        const status = container.State === 'running' ? 'running' : 'stopped';
                        html += '<div class="docker-container">';
                        html += '<span class="docker-status ' + status + '"></span>';
                        html += '<strong>' + (container.Name || container.Service || 'Unknown') + '</strong>';
                        html += '<p style="color: #8b8b9a; margin-top: 5px;">Status: ' + (container.State || 'unknown') + '</p>';
                        html += '</div>';
                    });
                } else if (data.daemon_running) {
                    html += '<p style="color: #8b8b9a;">No containers running</p>';
                }
                
                document.getElementById('dockerStatus').innerHTML = html;
            } catch (error) {
                document.getElementById('dockerStatus').innerHTML = '<p style="color: #ef4444;">Error: ' + error.message + '</p>';
            }
        }
        
        async function saveDockerImage() {
            const outputDiv = document.getElementById('saveImageOutput');
            outputDiv.innerHTML = '<p style="color: #f59e0b;">Saving image... This may take 1-2 minutes...</p>';
            
            try {
                const response = await fetch('/api/docker/save-image', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    outputDiv.innerHTML = '<p style="color: #10b981;">' + data.message + '</p>';
                } else {
                    outputDiv.innerHTML = '<p style="color: #ef4444;">Error: ' + data.error + '</p>';
                }
            } catch (error) {
                outputDiv.innerHTML = '<p style="color: #ef4444;">Error: ' + error.message + '</p>';
            }
        }
        
        async function dockerStart() {
            document.getElementById('dockerOutput').innerHTML = '<div class="loading"></div> Starting containers...';
            try {
                const response = await fetch(DASHBOARD_API + '/api/docker/start', {method: 'POST'});
                const data = await response.json();
                
                document.getElementById('dockerOutput').innerHTML = `
                    <div class="log-viewer">
                        <p>${data.success ? 'Containers started successfully' : 'Failed to start containers'}</p>
                        <pre>${data.output || data.error}</pre>
                    </div>
                `;
                
                setTimeout(dockerRefresh, 2000);
            } catch (error) {
                document.getElementById('dockerOutput').innerHTML = 
                    `<p style="color: #ef4444;">Error: ${error.message}</p>`;
            }
        }
        
        async function dockerStop() {
            document.getElementById('dockerOutput').innerHTML = '<div class="loading"></div> Stopping containers...';
            try {
                const response = await fetch(DASHBOARD_API + '/api/docker/stop', {method: 'POST'});
                const data = await response.json();
                
                document.getElementById('dockerOutput').innerHTML = `
                    <div class="log-viewer">
                        <p>${data.success ? 'Containers stopped successfully' : 'Failed to stop containers'}</p>
                        <pre>${data.output || data.error}</pre>
                    </div>
                `;
                
                setTimeout(dockerRefresh, 2000);
            } catch (error) {
                document.getElementById('dockerOutput').innerHTML = 
                    `<p style="color: #ef4444;">Error: ${error.message}</p>`;
            }
        }
        
        // Metrics
        async function loadMetrics() {
            try {
                const response = await fetch(DASHBOARD_API + '/api/metrics', {
                    cache: 'no-cache'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // Calculate success rate
                const successRate = data.total_requests > 0 
                    ? (data.successful_requests / data.total_requests * 100).toFixed(2)
                    : 0;
                
                document.getElementById('metricsContent').innerHTML = `
                    <div class="metric">
                        <span class="metric-label">Total Requests</span>
                        <span class="metric-value">${data.total_requests || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Successful</span>
                        <span class="metric-value">${data.successful_requests || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Failed</span>
                        <span class="metric-value">${data.failed_requests || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Success Rate</span>
                        <span class="metric-value">${successRate}%</span>
                    </div>
                `;
                
                document.getElementById('performanceMetrics').innerHTML = `
                    <div class="metric">
                        <span class="metric-label">Avg Latency</span>
                        <span class="metric-value">${data.average_latency_ms ? data.average_latency_ms.toFixed(2) : 0}ms</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Uptime</span>
                        <span class="metric-value">${data.uptime_seconds ? data.uptime_seconds.toFixed(0) : 0}s</span>
                    </div>
                    ${data.model_info ? `
                    <div class="metric">
                        <span class="metric-label">Model</span>
                        <span class="metric-value" style="font-size: 0.85em;">${data.model_info.status || 'unknown'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Device</span>
                        <span class="metric-value">${data.model_info.device || 'unknown'}</span>
                    </div>
                    ` : ''}
                `;
            } catch (error) {
                console.error('Metrics error:', error);
                document.getElementById('metricsContent').innerHTML = 
                    `<p style="color: #ef4444;">Error loading metrics: ${error.message}</p>`;
                document.getElementById('performanceMetrics').innerHTML = 
                    `<p style="color: #ef4444;">Error loading performance data</p>`;
            }
        }
        
        // Logs
        async function loadLogs(logType) {
            document.getElementById('logViewer').innerHTML = '<div class="loading"></div> Loading logs...';
            try {
                const response = await fetch(DASHBOARD_API + '/api/logs/' + logType + '?lines=100');
                const data = await response.json();
                
                if (data.logs && data.logs.length > 0) {
                    let html = '';
                    data.logs.forEach(line => {
                        html += '<div class="log-line">' + line + '</div>';
                    });
                    document.getElementById('logViewer').innerHTML = html;
                } else {
                    const errorMsg = data.error || 'No logs available';
                    document.getElementById('logViewer').innerHTML = '<p style="color: #8b8b9a;">No logs found or ' + errorMsg + '</p>';
                }
            } catch (error) {
                document.getElementById('logViewer').innerHTML = '<p style="color: #ef4444;">Error: ' + error.message + '</p>';
            }
        }
        
        // Tests
        async function runTests() {
            const output = document.getElementById('testOutput');
            output.style.display = 'block';
            output.innerHTML = '<div class="loading"></div> Running tests (this may take 10-15 seconds)...';
            
            try {
                const response = await fetch(DASHBOARD_API + '/api/run-tests', {
                    method: 'GET',
                    cache: 'no-cache'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // Count passed and failed
                const lines = data.output.split('\\n');
                const passedLine = lines.find(l => l.includes('passed'));
                const summary = passedLine || 'Check output below';
                
                output.innerHTML = `
                    <div style="padding: 15px; background: ${data.success ? '#1a3a2e' : '#3a1a1a'}; border-radius: 8px; margin-bottom: 15px;">
                        <p style="color: ${data.success ? '#10b981' : '#ef4444'}; font-size: 1.1em; font-weight: bold; margin-bottom: 5px;">
                            ${data.success ? '✓ All Tests Passed' : '⚠ Some Tests Failed'}
                        </p>
                        <p style="color: #8b8b9a; font-size: 0.9em;">${summary}</p>
                    </div>
                    <pre style="max-height: 400px; overflow-y: auto;">${data.output}</pre>
                `;
            } catch (error) {
                console.error('Test error:', error);
                output.innerHTML = `
                    <p style="color: #ef4444; margin-bottom: 10px;">Error running tests: ${error.message}</p>
                    <p style="color: #8b8b9a;">Check the console for details or try refreshing the page.</p>
                `;
            }
        }
        
        // Initialize when DOM is ready
        let systemInfoInterval = null;
        
        function initializeDashboard() {
            console.log('Dashboard initialized');
            loadSystemInfo();
            if (!systemInfoInterval) {
                systemInfoInterval = setInterval(loadSystemInfo, 10000); // Refresh every 10 seconds
            }
        }
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeDashboard);
        } else {
            // DOM is already ready
            initializeDashboard();
        }
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    print("Starting Enhanced Production Dashboard on http://localhost:3000")
    print("Features: System Info, Docker Management, Metrics, Logs, Tests")
    uvicorn.run(app, host="0.0.0.0", port=3000)
