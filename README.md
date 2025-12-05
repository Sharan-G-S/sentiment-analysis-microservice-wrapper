# Production Sentiment Analysis Wrapper

FastAPI microservice for sentiment analysis with DistilBERT, LLM enhancement, logging, and Docker deployment.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/Sharan-G-S/sentiment-analysis-microservice-wrapper.git
cd sentiment-analysis-microservice-wrapper
cp .env.example .env  # Add your API keys

# Start services
docker-compose up -d              # API (port 8000)
python3 dashboard_enhanced.py     # Dashboard (port 3000)
```

**Access:**
- API: http://localhost:8000/docs
- Dashboard: http://localhost:3000

---

## Features

- **Sentiment Analysis:** DistilBERT model with 97% accuracy
- **LLM Enhancement:** Detailed explanations via Groq/Gemini
- **Batch Processing:** Up to 100 texts at once
- **Docker Ready:** Containerized with health checks
- **Logging:** Structured logs for requests, errors, and metrics
- **Dashboard:** Web UI for testing and monitoring
- **Testing:** 17 tests, 58% coverage

---

## API Usage

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"This is amazing!","enhanced":true}'
```

**Response:**
```json
{
  "sentiment": "positive",
  "confidence": 0.9999,
  "enhanced_analysis": {
    "explanation": "Strong positive sentiment",
    "key_phrases": ["amazing"],
    "suggestions": ["Maintain quality"]
  },
  "latency_ms": 234
}
```

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | API documentation |
| POST | `/api/v1/predict` | Single prediction |
| POST | `/api/v1/predict/batch` | Batch predictions |

---

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI routes
│   ├── model.py             # DistilBERT wrapper
│   ├── llm_enhancer.py      # LLM integration
│   └── logger.py            # Logging system
├── tests/                    # 17 tests
├── docs/                     # Documentation
├── dashboard_enhanced.py     # Web dashboard
├── Dockerfile
└── docker-compose.yml
```

---

## Configuration

Create `.env` file:
```bash
GROQ_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
LOG_LEVEL=info
```

---

## Deployment

**Local:**
```bash
docker-compose up -d
```

**Production:**
```bash
docker build -t sentiment-api .
docker run -d -p 8000:8000 \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  --name sentiment-api \
  sentiment-api
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for AWS, Kubernetes, etc.

---

## Testing

```bash
pytest tests/ -v                    # Run all tests
pytest tests/ --cov=app             # With coverage
docker exec sentiment-api pytest    # In Docker
```

---

## Integration

**Python:**
```python
import requests
response = requests.post(
    "http://localhost:8000/api/v1/predict",
    json={"text": "Great product!"}
)
print(response.json()['sentiment'])
```

**Node.js:**
```javascript
const response = await axios.post(
    'http://localhost:8000/api/v1/predict',
    { text: 'Great product!' }
);
```

---

## Documentation

- [API Schema](docs/API_SCHEMA.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Integration Examples](docs/INTEGRATION.md)

---

## Performance

- Latency: <500ms
- Throughput: 1000+ req/min
- Accuracy: 97%
- Resources: 2GB RAM, 1 CPU

---

**Repository:** https://github.com/Sharan-G-S/sentiment-analysis-microservice-wrapper

---

Made with 💚 Sharan G S
