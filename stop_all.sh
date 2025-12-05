#!/bin/bash

# Production Wrapper Shutdown Script
# Stops all services: Docker API, Local API, and Dashboard

echo "======================================"
echo "Stopping Production Wrapper Services"
echo "======================================"
echo ""

# Stop Local API (Port 8001)
echo "[1/3] Stopping Local API (Port 8001)..."
lsof -ti:8001 | xargs kill -9 2>/dev/null && echo "✓ Local API stopped" || echo "⚠ Local API not running"

# Stop Dashboard (Port 3000)
echo "[2/3] Stopping Dashboard (Port 3000)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null && echo "✓ Dashboard stopped" || echo "⚠ Dashboard not running"

# Stop Docker container (Port 8000)
echo "[3/3] Stopping Docker container (Port 8000)..."
if command -v docker-compose &> /dev/null; then
    cd "/Users/sharan/Documents/September-AI/Production Wrapper New"
    docker-compose down 2>/dev/null && echo "✓ Docker container stopped" || echo "⚠ Docker container not running"
else
    echo "⚠ Docker not available"
fi

echo ""
echo "======================================"
echo "All Services Stopped"
echo "======================================"
