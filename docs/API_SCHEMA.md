# API Schema Documentation

## Overview
This document describes the complete API schema for the Sentiment Analysis microservice.

---

## Request Schemas

### PredictionRequest
Used for single text prediction.

```json
{
  "text": "string (required, 1-5000 chars)",
  "return_probabilities": "boolean (optional, default: false)",
  "request_id": "string (optional)"
}
```

**Validations:**
- `text` must not be empty or only whitespace
- `text` length between 1-5000 characters
- `return_probabilities` controls whether to include class probabilities

**Example:**
```json
{
  "text": "This product is amazing!",
  "return_probabilities": true,
  "request_id": "req_abc123"
}
```

---

### BatchPredictionRequest
Used for batch prediction of multiple texts.

```json
{
  "texts": ["string", "string", ...],
  "return_probabilities": "boolean (optional, default: false)",
  "request_id": "string (optional)"
}
```

**Validations:**
- `texts` must contain 1-100 items
- Each text follows same validation as single prediction
- Empty strings are filtered out

**Example:**
```json
{
  "texts": [
    "I love this product!",
    "This is terrible",
    "It's okay I guess"
  ],
  "return_probabilities": true
}
```

---

## Response Schemas

### PredictionResponse
Response for single prediction.

```json
{
  "sentiment": "string (positive|negative)",
  "confidence": "float (0.0-1.0)",
  "probabilities": {
    "positive": "float (0.0-1.0)",
    "negative": "float (0.0-1.0)"
  } | null,
  "latency_ms": "float",
  "request_id": "string | null",
  "timestamp": "string (ISO 8601)"
}
```

**Example:**
```json
{
  "sentiment": "positive",
  "confidence": 0.9876,
  "probabilities": {
    "positive": 0.9876,
    "negative": 0.0124
  },
  "latency_ms": 45.23,
  "request_id": "req_abc123",
  "timestamp": "2025-12-04T10:30:00.123Z"
}
```

---

### BatchPredictionResponse
Response for batch prediction.

```json
{
  "predictions": [
    {
      "sentiment": "string",
      "confidence": "float",
      "probabilities": "object | null",
      "latency_ms": "float",
      "request_id": "string",
      "timestamp": "string"
    }
  ],
  "total_latency_ms": "float",
  "request_id": "string | null"
}
```

---

### HealthResponse
Response from health check endpoint.

```json
{
  "status": "string (healthy|unhealthy)",
  "model_loaded": "boolean",
  "version": "string",
  "timestamp": "string (ISO 8601)"
}
```

---

### MetricsResponse
Response from metrics endpoint.

```json
{
  "total_requests": "integer",
  "successful_requests": "integer",
  "failed_requests": "integer",
  "average_latency_ms": "float",
  "uptime_seconds": "float",
  "model_info": {
    "model_name": "string",
    "device": "string (cpu|cuda)",
    "status": "string (loaded|not_loaded)",
    "framework": "string"
  }
}
```

---

## Error Responses

### Validation Error (422)
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Service Unavailable (503)
```json
{
  "detail": "Model not loaded"
}
```

### Internal Server Error (500)
```json
{
  "detail": "Prediction failed: <error message>"
}
```

---

## OpenAPI Specification

The full OpenAPI (Swagger) specification is available at:
- **JSON**: http://localhost:8000/openapi.json
- **Interactive UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
