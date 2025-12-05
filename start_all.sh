#!/bin/bash

# Production Wrapper Startup Script
# Starts all services: Docker API, Local API, and Dashboard

PROJECT_DIR="/Users/sharan/Documents/September-AI/Production Wrapper New"
cd "$PROJECT_DIR"

echo "======================================"
echo "Starting Production Wrapper Services"
echo "======================================"
echo ""

# Activate virtual environment
echo "[1/4] Activating virtual environment..."
source venv/bin/activate

# Start Docker container (Port 8000) - Optional
echo "[2/4] Starting Docker container (Port 8000)..."
if command -v docker-compose &> /dev/null; then
    if docker info &> /dev/null; then
        docker-compose up -d 2>/dev/null && echo "✓ Docker container started" || echo "⚠ Docker container failed to start"
    else
        echo "⚠ Docker daemon not running - Start Docker Desktop to use containerized deployment"
        echo "  Continuing with local API only..."
    fi
else
    echo "⚠ Docker not installed, skipping container startup"
fi

# Wait for Docker to be ready
sleep 2

# Start Local API (Port 8001)
echo "[3/4] Starting Local API (Port 8001)..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > api_server.log 2>&1 &
API_PID=$!
echo "✓ Local API started (PID: $API_PID)"

# Wait for API to be ready
sleep 3

# Start Dashboard (Port 3000)
echo "[4/4] Starting Dashboard (Port 3000)..."
nohup python dashboard_enhanced.py > dashboard_enhanced.log 2>&1 &
DASHBOARD_PID=$!
echo "✓ Dashboard started (PID: $DASHBOARD_PID)"

# Wait for Dashboard to be ready
sleep 3

echo ""
echo "======================================"
echo "Services Started Successfully!"
echo "======================================"
echo ""
echo "Active Services:"
if docker ps --filter "name=sentiment-api" --format "{{.Names}}" 2>/dev/null | grep -q sentiment-api; then
    echo "  ✓ Docker API:    http://localhost:8000"
else
    echo "  ✗ Docker API:    Not running (Docker daemon not available)"
fi
echo "  ✓ Local API:     http://localhost:8001"
echo "  ✓ Dashboard:     http://localhost:3000"
echo ""
echo "API Documentation:"
echo "  • Docker API:    http://localhost:8000/docs"
echo "  • Local API:     http://localhost:8001/docs"
echo ""
echo "Process IDs:"
echo "  • Local API PID: $API_PID"
echo "  • Dashboard PID: $DASHBOARD_PID"
echo ""
echo "Log Files:"
echo "  • Local API:     api_server.log"
echo "  • Dashboard:     dashboard_enhanced.log"
echo "  • Docker:        docker-compose logs -f"
echo ""
echo "To stop all services, run: ./stop_all.sh"
echo "======================================"
