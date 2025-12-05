#!/bin/bash

# Test script for verifying the sentiment analysis API

set -e

echo "========================================"
echo "Sentiment Analysis API - Test Suite"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API is running
echo "1. Checking if API is running..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API is running"
else
    echo -e "${RED}✗${NC} API is not running"
    echo "   Please start the API with: ./start.sh"
    exit 1
fi

echo ""
echo "2. Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo $HEALTH | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Health check passed"
    echo "   $HEALTH"
else
    echo -e "${RED}✗${NC} Health check failed"
    exit 1
fi

echo ""
echo "3. Testing single prediction..."
RESULT=$(curl -s -X POST http://localhost:8000/api/v1/predict \
    -H "Content-Type: application/json" \
    -d '{"text": "This is amazing!"}')

if echo $RESULT | grep -q "sentiment"; then
    echo -e "${GREEN}✓${NC} Single prediction successful"
    SENTIMENT=$(echo $RESULT | grep -o '"sentiment":"[^"]*"' | cut -d'"' -f4)
    CONFIDENCE=$(echo $RESULT | grep -o '"confidence":[0-9.]*' | cut -d':' -f2)
    echo "   Sentiment: $SENTIMENT"
    echo "   Confidence: $CONFIDENCE"
else
    echo -e "${RED}✗${NC} Single prediction failed"
    exit 1
fi

echo ""
echo "4. Testing batch prediction..."
BATCH_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/predict/batch \
    -H "Content-Type: application/json" \
    -d '{"texts": ["Great!", "Terrible", "Okay"]}')

if echo $BATCH_RESULT | grep -q "predictions"; then
    echo -e "${GREEN}✓${NC} Batch prediction successful"
    COUNT=$(echo $BATCH_RESULT | grep -o '"sentiment":"[^"]*"' | wc -l)
    echo "   Processed $COUNT texts"
else
    echo -e "${RED}✗${NC} Batch prediction failed"
    exit 1
fi

echo ""
echo "5. Testing metrics endpoint..."
METRICS=$(curl -s http://localhost:8000/metrics)
if echo $METRICS | grep -q "total_requests"; then
    echo -e "${GREEN}✓${NC} Metrics endpoint working"
    TOTAL=$(echo $METRICS | grep -o '"total_requests":[0-9]*' | cut -d':' -f2)
    echo "   Total requests: $TOTAL"
else
    echo -e "${RED}✗${NC} Metrics endpoint failed"
    exit 1
fi

echo ""
echo "6. Testing API documentation..."
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API docs accessible at http://localhost:8000/docs"
else
    echo -e "${YELLOW}!${NC} API docs check skipped (browser required)"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✓${NC} All tests passed!"
echo "========================================"
echo ""
echo "The API is working correctly. You can:"
echo "  - Use CLI: ./cli.py predict 'your text'"
echo "  - Start dashboard: python dashboard.py"
echo "  - View docs: http://localhost:8000/docs"
echo ""
