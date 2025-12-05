# Docker Usage Guide

## What is Docker in This Project?

Docker is used to containerize the sentiment analysis API, packaging the entire application (code, dependencies, model) into an isolated container that runs consistently across any environment.

## Why Docker is Used Here

### Problem It Solves
1. **macOS PyTorch Issue**: The DistilBERT model causes bus errors on macOS M-series chips. Docker uses Linux internally, avoiding this issue.
2. **Environment Consistency**: Same behavior on macOS, Windows, Linux, cloud servers.
3. **Dependency Isolation**: Python packages and model don't interfere with your system.
4. **Easy Deployment**: Single command to run on any server.

### What Gets Containerized
- FastAPI application (app/main.py)
- DistilBERT sentiment model
- Python dependencies (transformers, torch, etc.)
- LLM integration (Groq, Gemini)
- Logging system
- Metrics endpoint

## Docker Architecture

```
Docker Container (Linux environment)
├── Python 3.11
├── FastAPI API Server (port 8000)
├── DistilBERT Model (auto-downloaded on first run)
├── LLM Enhancer (Groq + Gemini)
└── Logging system

Your Computer (macOS)
├── Docker Engine (runs the container)
├── Dashboard (port 3000) - connects to container
└── Access API at http://localhost:8000
```

## How to Use Docker

### 1. Start the Container

```bash
docker-compose up -d
```

What happens:
- Builds Docker image (first time: downloads Python, installs packages)
- Downloads DistilBERT model (268MB, ~2 minutes first time)
- Starts API server on port 8000
- Runs health checks every 30 seconds
- Container runs in background (`-d` flag)

### 2. Check Container Status

```bash
# List running containers
docker ps

# Should show:
# CONTAINER ID   STATUS                 PORTS                    NAMES
# xxxxxxxxxxxx   Up X minutes (healthy) 0.0.0.0:8000->8000/tcp   sentiment-api
```

### 3. View Logs

```bash
# Follow logs in real-time
docker logs -f sentiment-api

# View last 100 lines
docker logs --tail 100 sentiment-api

# View logs from last 5 minutes
docker logs --since 5m sentiment-api
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Make prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"This product is amazing!"}'
```

### 5. Stop the Container

```bash
# Stop container (data preserved)
docker-compose down

# Stop and remove everything (fresh start next time)
docker-compose down -v
```

### 6. Restart the Container

```bash
# Restart without rebuilding
docker-compose restart

# Rebuild and restart (after code changes)
docker-compose up -d --build
```

### 7. Access Container Shell

```bash
# Open bash inside container
docker exec -it sentiment-api bash

# Run commands inside container
docker exec sentiment-api ls -la /app
docker exec sentiment-api cat /app/logs/app.log
```

### 8. Run Tests Inside Container

```bash
# Run all tests (including model tests that fail on macOS)
docker exec sentiment-api pytest tests/ -v

# Run with coverage
docker exec sentiment-api pytest tests/ --cov=app
```

## Configuration Files

### docker-compose.yml
Orchestrates the container setup:

```yaml
services:
  sentiment-api:
    build: .                    # Build from Dockerfile
    container_name: sentiment-api
    ports:
      - "8000:8000"             # Map container port 8000 to host port 8000
    environment:
      - GROQ_API_KEY=xxx        # LLM API keys
      - GOOGLE_API_KEY=xxx
    restart: unless-stopped      # Auto-restart on crash
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s             # Check every 30 seconds
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'             # Max 2 CPU cores
          memory: 4G            # Max 4GB RAM
```

### Dockerfile
Defines how to build the container image:

```dockerfile
FROM python:3.11-slim           # Base image: Python 3.11 on Debian
WORKDIR /app                    # Set working directory

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user (security)
RUN useradd -m appuser
USER appuser

EXPOSE 8000                     # Document exposed port

# Start API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Common Docker Commands

### Container Management
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Rebuild
docker-compose up -d --build

# View status
docker ps
docker ps -a  # Include stopped containers
```

### Logs
```bash
# All logs
docker logs sentiment-api

# Follow logs
docker logs -f sentiment-api

# Last N lines
docker logs --tail 50 sentiment-api

# Since timestamp
docker logs --since "2025-12-05T10:00:00" sentiment-api
```

### Resource Usage
```bash
# CPU, memory usage
docker stats sentiment-api

# Disk usage
docker system df
```

### Cleanup
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove everything unused
docker system prune -a
```

## Port Mapping

The container exposes port 8000 internally. Docker maps it to your computer:

```
Container (inside):  0.0.0.0:8000 (API server)
                     ↓ (mapped via Docker)
Your Computer:       localhost:8000 (accessible from browser/dashboard)
```

Dashboard on port 3000 connects to localhost:8000, which Docker forwards to the container.

## Environment Variables

Set in docker-compose.yml:

```yaml
environment:
  - LOG_LEVEL=info                    # Logging verbosity
  - GROQ_API_KEY=gsk_xxx             # Groq LLM API key
  - GOOGLE_API_KEY=AIzaSyxxx          # Gemini API key
```

To update API keys:
1. Edit docker-compose.yml
2. Restart: `docker-compose up -d --force-recreate`

## Health Checks

Docker automatically monitors container health:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s      # Check every 30 seconds
  timeout: 10s       # Fail if takes >10 seconds
  retries: 3         # Mark unhealthy after 3 failures
  start_period: 40s  # Grace period on startup
```

Check health:
```bash
docker ps
# Look for "(healthy)" in STATUS column
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs for errors
docker logs sentiment-api

# Check if port 8000 is already in use
lsof -i :8000

# Remove and recreate
docker-compose down
docker-compose up -d --build
```

### Model Not Loading
```bash
# Check logs
docker logs sentiment-api | grep -i "model"

# Ensure enough memory (needs 2-4GB)
docker stats sentiment-api

# Restart with more memory
# Edit docker-compose.yml: memory: 4G
docker-compose up -d --force-recreate
```

### API Unreachable
```bash
# Check container is running
docker ps | grep sentiment-api

# Check health status
docker inspect sentiment-api | grep -A 5 "Health"

# Test from inside container
docker exec sentiment-api curl http://localhost:8000/health
```

### Tests Fail on macOS
```bash
# Run tests inside Docker (Linux environment)
docker exec sentiment-api pytest tests/ -v

# All 22 tests should pass inside container
```

## Deployment Scenarios

### Development (Current Setup)
```bash
docker-compose up -d
# API: http://localhost:8000
# Dashboard: http://localhost:3000
```

### Production (Single Server)
```bash
# Use production-ready settings
docker-compose -f docker-compose.prod.yml up -d

# Behind reverse proxy (nginx)
# nginx forwards requests to localhost:8000
```

### Production (Kubernetes)
```bash
# Scale to multiple replicas
kubectl apply -f deployment.yaml
kubectl scale deployment sentiment-api --replicas=5

# Load balancer distributes traffic
```

## Performance

### Resource Allocation
- CPU: 1-2 cores recommended
- Memory: 2GB minimum, 4GB recommended
- Disk: ~1GB (model + dependencies)

### Startup Time
- First run: 2-3 minutes (downloads model)
- Subsequent runs: 30-60 seconds (model cached)

### Request Latency
- Inside container: 50-200ms
- Through Docker networking: +5-10ms overhead

## Security

### Current Setup
- Non-root user (appuser) runs the application
- No privileged access
- API keys in environment (not in code)
- Health checks prevent zombie containers

### Recommendations for Production
- Use Docker secrets for API keys
- Enable TLS/HTTPS
- Add authentication middleware
- Run vulnerability scans: `docker scan sentiment-api`

## Comparison: Docker vs Local

| Aspect | Docker Container | Local Python |
|--------|-----------------|--------------|
| Setup | `docker-compose up -d` | Install Python, pip, dependencies |
| macOS Compatibility | Works (Linux inside) | Fails (PyTorch bus error) |
| Isolation | Complete | Shared with system |
| Portability | Deploy anywhere | Requires Python setup |
| Resource Control | Set CPU/memory limits | Uses all available |
| Deployment | `docker push` to registry | Manual deployment |

## Quick Reference

```bash
# Start project
docker-compose up -d

# Check status
docker ps

# View logs
docker logs -f sentiment-api

# Test API
curl http://localhost:8000/health

# Run tests
docker exec sentiment-api pytest tests/ -v

# Stop project
docker-compose down

# Restart after code changes
docker-compose up -d --build
```

## Integration with Dashboard

The dashboard (dashboard_enhanced.py) runs directly on your computer (not in Docker) and connects to the Dockerized API:

```
Dashboard (port 3000)  ──HTTP──>  Docker Container (port 8000)
  - Python script              - FastAPI server
  - Runs on macOS              - Runs in Linux
  - Serves web UI              - Serves API endpoints
```

This architecture allows:
- Dashboard to run without Docker dependencies
- API to run in stable Linux environment (avoiding macOS issues)
- Easy development (edit dashboard, no container rebuild)

## Next Steps

1. **Start the project**: `docker-compose up -d`
2. **Verify health**: `docker ps` (should show "healthy")
3. **View logs**: `docker logs -f sentiment-api`
4. **Test API**: `curl http://localhost:8000/health`
5. **Access dashboard**: http://localhost:3000
6. **Run tests**: `docker exec sentiment-api pytest tests/ -v`
