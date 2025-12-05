# Deployment Guide

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Production Checklist](#production-checklist)

---

## Local Development

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

```bash
export LOG_LEVEL=info
export MODEL_CACHE_DIR=/path/to/cache
```

---

## Docker Deployment

### Build Image

```bash
docker build -t sentiment-api:latest .
```

### Run Container

```bash
docker run -d \
  --name sentiment-api \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  sentiment-api:latest
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.19+)
- kubectl configured
- Docker registry access

### Steps

1. **Push image to registry**
```bash
docker tag sentiment-api:latest your-registry/sentiment-api:latest
docker push your-registry/sentiment-api:latest
```

2. **Apply manifests**
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

3. **Verify deployment**
```bash
kubectl get pods
kubectl get services
```

### Auto-scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sentiment-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sentiment-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Cloud Deployment

### AWS ECS/Fargate

1. **Create ECR repository**
```bash
aws ecr create-repository --repository-name sentiment-api
```

2. **Push image**
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag sentiment-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/sentiment-api:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/sentiment-api:latest
```

3. **Create task definition** (JSON file)
```json
{
  "family": "sentiment-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [{
    "name": "sentiment-api",
    "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/sentiment-api:latest",
    "portMappings": [{
      "containerPort": 8000,
      "protocol": "tcp"
    }],
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
      "interval": 30,
      "timeout": 10,
      "retries": 3
    }
  }]
}
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/sentiment-api

# Deploy
gcloud run deploy sentiment-api \
  --image gcr.io/PROJECT_ID/sentiment-api \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --allow-unauthenticated \
  --max-instances 10
```

### Azure Container Instances

```bash
# Create resource group
az group create --name sentiment-api-rg --location eastus

# Create container
az container create \
  --resource-group sentiment-api-rg \
  --name sentiment-api \
  --image sentiment-api:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --ip-address public \
  --dns-name-label sentiment-api
```

---

## Production Checklist

### Before Deployment

- [ ] Run full test suite (`pytest tests/`)
- [ ] Verify Docker build (`docker build -t sentiment-api:latest .`)
- [ ] Test container locally (`docker run -p 8000:8000 sentiment-api:latest`)
- [ ] Check health endpoint (`curl http://localhost:8000/health`)
- [ ] Review resource limits (CPU, memory)
- [ ] Configure logging destinations
- [ ] Set up monitoring/alerting
- [ ] Review CORS settings
- [ ] Configure rate limiting (if needed)
- [ ] Set up SSL/TLS certificates
- [ ] Document API endpoints

### Security

- [ ] Use non-root user in container ✅ (already configured)
- [ ] Scan image for vulnerabilities (`docker scan sentiment-api:latest`)
- [ ] Enable HTTPS/TLS
- [ ] Add API authentication (if required)
- [ ] Review firewall rules
- [ ] Enable audit logging
- [ ] Rotate secrets regularly

### Monitoring

- [ ] Set up health check monitoring
- [ ] Configure log aggregation (ELK, CloudWatch, etc.)
- [ ] Set up metrics collection
- [ ] Create dashboards (Grafana, Datadog, etc.)
- [ ] Configure alerts for errors/latency
- [ ] Monitor resource usage

### Backup & Recovery

- [ ] Document rollback procedure
- [ ] Test disaster recovery
- [ ] Set up log retention policy
- [ ] Document incident response process

---

## Scaling Strategies

### Horizontal Scaling
Deploy multiple instances behind a load balancer:

```
        ┌─────────────┐
        │Load Balancer│
        └──────┬──────┘
               │
       ┌───────┼───────┐
       │       │       │
    ┌──▼──┐ ┌──▼──┐ ┌──▼──┐
    │API 1│ │API 2│ │API 3│
    └─────┘ └─────┘ └─────┘
```

### Vertical Scaling
Increase resources per instance:
- CPU: 2-4 cores
- Memory: 4-8GB
- Use GPU for 10-20x speedup

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs sentiment-api

# Inspect container
docker inspect sentiment-api
```

### High memory usage
- Check for memory leaks in logs
- Reduce batch sizes
- Increase container memory limits

### Slow responses
- Enable GPU if available
- Use caching for repeated queries
- Check network latency
- Review model quantization

---

## Support

For deployment issues:
1. Check logs in `logs/` directory
2. Review health check status
3. Verify resource availability
4. Consult troubleshooting section in README
