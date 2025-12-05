# Quick Start - One Command Demo

## For Demo/Presentation

### Single Command to Start Everything:

```bash
./start.sh
```

This starts:
- Docker API container (port 8000)
- Dashboard web interface (port 3000)
- Automatically opens http://localhost:3000

### Demo Workflow:

1. Navigate to project directory
2. Run `./start.sh`
3. Wait for "Production Wrapper - Ready!" message
4. Dashboard opens automatically in browser
5. Show features: Predictions, Metrics, Logs, Tests

### To Stop:

```bash
./stop_all.sh
```

## What Happens During Startup

```
[1/2] Starting Docker API (port 8000)...
      - Checks Docker is running
      - Starts sentiment-api container
      - Waits for model to load
      - Verifies health check passes

[2/2] Starting Dashboard (port 3000)...
      - Starts web interface
      - Connects to Docker API
      - Opens browser automatically

Production Wrapper - Ready!
```

## Timing

- First run: ~2 minutes (downloads DistilBERT model)
- Subsequent runs: ~30 seconds
- Dashboard ready in: ~5 seconds after API is healthy

## Access Points

After running `./start.sh`:

- **Dashboard**: http://localhost:3000 (main demo interface)
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)

## Troubleshooting

### Docker Not Running
```
ERROR: Docker is not running
Please start Docker Desktop and try again
```
**Solution**: Start Docker Desktop, wait for it to be ready, run `./start.sh` again

### Port Already In Use
```
Error: port is already allocated
```
**Solution**: Run `./stop_all.sh` first, then `./start.sh`

### Model Loading Takes Time
```
Waiting for model to load...
```
**Normal**: First time downloads 268MB model (~2 min). Subsequent runs use cached model (~30 sec)

## Manual Commands (Alternative)

If you prefer manual control:

```bash
# Start Docker API
docker-compose up -d

# Start Dashboard
python3 dashboard_enhanced.py
```

Access: http://localhost:3000

## Features to Demonstrate

After running `./start.sh`, demonstrate these tabs in dashboard:

1. **Overview** - System status, model info
2. **Predictions** - Real-time sentiment analysis
3. **Docker** - Container management
4. **Metrics** - Performance statistics
5. **Logs** - Application, prediction, error logs
6. **Tests** - Run all 22 automated tests

## Sample Demo Script

```
1. Run ./start.sh
2. Wait for browser to open
3. Show Overview tab - model loaded, system healthy
4. Go to Predictions tab
5. Enter: "This product is amazing and exceeded expectations!"
6. Click Predict (with Enhanced Analysis checked)
7. Show sentiment result + LLM explanation
8. Go to Metrics tab - show request counts, latency
9. Go to Logs tab - show prediction log entry
10. Go to Tests tab - click "Run All Tests" - show 22 passing
```

## Quick Commands Reference

```bash
# Start everything
./start.sh

# Stop everything
./stop_all.sh

# Check status
docker ps
curl http://localhost:8000/health

# View logs
docker logs -f sentiment-api

# Run tests
docker exec sentiment-api pytest tests/ -v
```

## Requirements

- Docker Desktop installed and running
- Python 3.8+ installed
- 4GB RAM available for Docker
- Ports 3000 and 8000 available
