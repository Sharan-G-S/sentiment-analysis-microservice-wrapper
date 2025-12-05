#!/bin/bash

# Production Wrapper - Single Command Startup
# Starts Docker API and Dashboard

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "Production Wrapper - Starting Services"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Start Docker API
echo "[1/2] Starting Docker API (port 8000)..."
docker-compose up -d
echo "      Waiting for API to be healthy..."
sleep 5

# Check Docker container health
if docker ps --filter "name=sentiment-api" --filter "health=healthy" --format "{{.Names}}" | grep -q sentiment-api; then
    echo "      Docker API is healthy"
else
    echo "      Waiting for model to load..."
    sleep 30
fi

# Start Dashboard
echo "[2/2] Starting Dashboard (port 3000)..."
pkill -f dashboard_enhanced.py 2>/dev/null || true
nohup python3 dashboard_enhanced.py > /dev/null 2>&1 &
DASHBOARD_PID=$!
sleep 3

echo ""
echo "=========================================="
echo "Production Wrapper - Ready!"
echo "=========================================="
echo ""
echo "Access Points:"
echo "  Dashboard:     http://localhost:3000"
echo "  API:           http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo ""
echo "Status:"
docker ps --filter "name=sentiment-api" --format "  Container:     {{.Names}} ({{.Status}})"
ps aux | grep dashboard_enhanced.py | grep -v grep | awk '{print "  Dashboard:     Running (PID: " $2 ")"}'
echo ""
echo "To stop: ./stop_all.sh"
echo "=========================================="
echo ""
echo "Opening dashboard in browser..."
sleep 2
open http://localhost:3000 2>/dev/null || echo "Open http://localhost:3000 in your browser"
