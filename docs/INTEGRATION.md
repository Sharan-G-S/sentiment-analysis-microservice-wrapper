# Integration Guide

## Table of Contents
1. [Overview](#overview)
2. [Client Libraries](#client-libraries)
3. [Integration Patterns](#integration-patterns)
4. [Use Cases](#use-cases)
5. [Best Practices](#best-practices)

---

## Overview

This guide shows how to integrate the Sentiment Analysis API into your applications.

**Base URL**: `http://localhost:8000` (development) or your deployed endpoint

---

## Client Libraries

### Python Client

```python
import requests
from typing import Optional, List, Dict

class SentimentAPIClient:
    """Python client for Sentiment Analysis API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def predict(
        self,
        text: str,
        return_probabilities: bool = False,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Predict sentiment for text
        
        Args:
            text: Text to analyze
            return_probabilities: Include class probabilities
            request_id: Optional tracking ID
            
        Returns:
            Prediction result
        """
        payload = {
            "text": text,
            "return_probabilities": return_probabilities
        }
        if request_id:
            payload["request_id"] = request_id
        
        response = self.session.post(
            f"{self.base_url}/api/v1/predict",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def predict_batch(
        self,
        texts: List[str],
        return_probabilities: bool = False
    ) -> Dict:
        """Predict sentiment for multiple texts"""
        payload = {
            "texts": texts,
            "return_probabilities": return_probabilities
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/predict/batch",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> Dict:
        """Get API metrics"""
        response = self.session.get(f"{self.base_url}/metrics")
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == "__main__":
    client = SentimentAPIClient()
    
    # Single prediction
    result = client.predict("This product is amazing!", return_probabilities=True)
    print(f"Sentiment: {result['sentiment']}")
    print(f"Confidence: {result['confidence']:.2%}")
    
    # Batch prediction
    texts = ["Great!", "Terrible", "Okay"]
    batch_result = client.predict_batch(texts)
    for pred in batch_result['predictions']:
        print(f"{pred['sentiment']}: {pred['confidence']:.2%}")
```

### JavaScript/TypeScript Client

```typescript
interface PredictionRequest {
  text: string;
  return_probabilities?: boolean;
  request_id?: string;
}

interface PredictionResponse {
  sentiment: 'positive' | 'negative';
  confidence: number;
  probabilities?: {
    positive: number;
    negative: number;
  };
  latency_ms: number;
  request_id?: string;
  timestamp: string;
}

class SentimentAPIClient {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL.replace(/\/$/, '');
  }

  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseURL}/health`);
    if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
    return response.json();
  }

  async predict(
    text: string,
    returnProbabilities: boolean = false,
    requestId?: string
  ): Promise<PredictionResponse> {
    const body: PredictionRequest = {
      text,
      return_probabilities: returnProbabilities,
    };
    if (requestId) body.request_id = requestId;

    const response = await fetch(`${this.baseURL}/api/v1/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) throw new Error(`Prediction failed: ${response.status}`);
    return response.json();
  }

  async predictBatch(
    texts: string[],
    returnProbabilities: boolean = false
  ): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/v1/predict/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        texts,
        return_probabilities: returnProbabilities,
      }),
    });

    if (!response.ok) throw new Error(`Batch prediction failed: ${response.status}`);
    return response.json();
  }
}

// Usage
const client = new SentimentAPIClient();

const result = await client.predict('This is awesome!', true);
console.log(`Sentiment: ${result.sentiment}`);
console.log(`Confidence: ${(result.confidence * 100).toFixed(2)}%`);
```

### Go Client

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

type PredictionRequest struct {
    Text                string  `json:"text"`
    ReturnProbabilities bool    `json:"return_probabilities"`
    RequestID           *string `json:"request_id,omitempty"`
}

type PredictionResponse struct {
    Sentiment     string             `json:"sentiment"`
    Confidence    float64            `json:"confidence"`
    Probabilities map[string]float64 `json:"probabilities,omitempty"`
    LatencyMs     float64            `json:"latency_ms"`
    RequestID     *string            `json:"request_id,omitempty"`
    Timestamp     string             `json:"timestamp"`
}

type SentimentClient struct {
    BaseURL string
    Client  *http.Client
}

func NewSentimentClient(baseURL string) *SentimentClient {
    return &SentimentClient{
        BaseURL: baseURL,
        Client:  &http.Client{},
    }
}

func (c *SentimentClient) Predict(text string, returnProbs bool) (*PredictionResponse, error) {
    reqBody := PredictionRequest{
        Text:                text,
        ReturnProbabilities: returnProbs,
    }

    jsonData, err := json.Marshal(reqBody)
    if err != nil {
        return nil, err
    }

    resp, err := c.Client.Post(
        c.BaseURL+"/api/v1/predict",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result PredictionResponse
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }

    return &result, nil
}

func main() {
    client := NewSentimentClient("http://localhost:8000")
    
    result, err := client.Predict("This is great!", true)
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Sentiment: %s\n", result.Sentiment)
    fmt.Printf("Confidence: %.2f%%\n", result.Confidence*100)
}
```

---

## Integration Patterns

### 1. Real-time Feedback Analysis

```python
# Analyze customer feedback as it comes in
def process_customer_feedback(feedback: str, customer_id: str):
    client = SentimentAPIClient()
    
    # Analyze sentiment
    result = client.predict(
        text=feedback,
        request_id=f"customer_{customer_id}"
    )
    
    # Route based on sentiment
    if result['sentiment'] == 'negative' and result['confidence'] > 0.8:
        # Urgent: route to support team
        escalate_to_support(feedback, customer_id)
    
    # Store for analytics
    store_sentiment_data(customer_id, result)
    
    return result
```

### 2. Batch Processing

```python
# Process large volumes of text data
def analyze_review_batch(reviews: List[str]):
    client = SentimentAPIClient()
    
    # Process in batches of 100
    batch_size = 100
    results = []
    
    for i in range(0, len(reviews), batch_size):
        batch = reviews[i:i+batch_size]
        batch_result = client.predict_batch(batch)
        results.extend(batch_result['predictions'])
    
    return results
```

### 3. Microservices Architecture

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()
sentiment_client = SentimentAPIClient()

@app.post("/reviews")
async def create_review(review: str, background_tasks: BackgroundTasks):
    """Create review and analyze sentiment in background"""
    
    # Store review immediately
    review_id = store_review(review)
    
    # Analyze sentiment in background
    background_tasks.add_task(
        analyze_and_update,
        review_id,
        review
    )
    
    return {"review_id": review_id, "status": "processing"}

def analyze_and_update(review_id: str, text: str):
    result = sentiment_client.predict(text)
    update_review_sentiment(review_id, result)
```

### 4. Stream Processing (Kafka)

```python
from kafka import KafkaConsumer, KafkaProducer
import json

# Consumer for incoming messages
consumer = KafkaConsumer(
    'user_feedback',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Producer for sentiment results
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

client = SentimentAPIClient()

for message in consumer:
    feedback = message.value['text']
    
    # Analyze sentiment
    result = client.predict(feedback)
    
    # Publish to results topic
    producer.send('sentiment_results', {
        'original': message.value,
        'sentiment': result
    })
```

---

## Use Cases

### 1. Customer Support Triage

```python
def triage_support_ticket(ticket_text: str, ticket_id: str):
    """Automatically prioritize support tickets"""
    client = SentimentAPIClient()
    result = client.predict(ticket_text, return_probabilities=True)
    
    priority = 'low'
    if result['sentiment'] == 'negative':
        if result['confidence'] > 0.9:
            priority = 'urgent'
        elif result['confidence'] > 0.7:
            priority = 'high'
    
    update_ticket_priority(ticket_id, priority)
    return priority
```

### 2. Social Media Monitoring

```python
def monitor_brand_mentions(mentions: List[str]):
    """Track brand sentiment on social media"""
    client = SentimentAPIClient()
    results = client.predict_batch(mentions)
    
    sentiment_scores = [p['confidence'] if p['sentiment'] == 'positive' 
                       else -p['confidence'] 
                       for p in results['predictions']]
    
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    if avg_sentiment < -0.5:
        send_alert("Negative brand sentiment detected!")
    
    return {
        'average_sentiment': avg_sentiment,
        'total_mentions': len(mentions),
        'positive': sum(1 for s in sentiment_scores if s > 0),
        'negative': sum(1 for s in sentiment_scores if s < 0)
    }
```

### 3. Product Review Analysis

```python
def analyze_product_reviews(product_id: str):
    """Aggregate sentiment for product reviews"""
    reviews = fetch_reviews(product_id)
    client = SentimentAPIClient()
    
    results = client.predict_batch([r['text'] for r in reviews])
    
    # Calculate aggregate metrics
    positive_count = sum(1 for p in results['predictions'] 
                        if p['sentiment'] == 'positive')
    
    avg_confidence = sum(p['confidence'] for p in results['predictions']) / len(results['predictions'])
    
    return {
        'product_id': product_id,
        'total_reviews': len(reviews),
        'positive_percentage': (positive_count / len(reviews)) * 100,
        'avg_confidence': avg_confidence,
        'sentiment_score': calculate_overall_score(results['predictions'])
    }
```

### 4. Content Moderation

```python
def moderate_user_content(content: str, user_id: str):
    """Flag negative content for review"""
    client = SentimentAPIClient()
    result = client.predict(content)
    
    if result['sentiment'] == 'negative' and result['confidence'] > 0.85:
        # Flag for manual review
        flag_for_moderation(content, user_id, result)
        return {'approved': False, 'reason': 'negative_sentiment'}
    
    return {'approved': True}
```

---

## Best Practices

### 1. Error Handling

```python
import time
from requests.exceptions import RequestException

def predict_with_retry(text: str, max_retries: int = 3):
    """Predict with exponential backoff retry"""
    client = SentimentAPIClient()
    
    for attempt in range(max_retries):
        try:
            return client.predict(text)
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Retry {attempt + 1} after {wait_time}s")
            time.sleep(wait_time)
```

### 2. Caching

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def predict_cached(text_hash: str, text: str):
    """Cache predictions for frequently analyzed texts"""
    client = SentimentAPIClient()
    return client.predict(text)

def predict(text: str):
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return predict_cached(text_hash, text)
```

### 3. Rate Limiting

```python
from time import sleep, time

class RateLimitedClient:
    def __init__(self, requests_per_second: int = 10):
        self.client = SentimentAPIClient()
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0
    
    def predict(self, text: str):
        # Wait if needed to respect rate limit
        elapsed = time() - self.last_request
        if elapsed < self.min_interval:
            sleep(self.min_interval - elapsed)
        
        result = self.client.predict(text)
        self.last_request = time()
        return result
```

### 4. Async Operations

```python
import asyncio
import aiohttp

async def predict_async(text: str):
    """Async prediction for high throughput"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/api/v1/predict',
            json={'text': text}
        ) as response:
            return await response.json()

async def process_many_texts(texts: List[str]):
    """Process multiple texts concurrently"""
    tasks = [predict_async(text) for text in texts]
    return await asyncio.gather(*tasks)
```

### 5. Monitoring Integration

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def predict_with_logging(text: str):
    """Log all API calls for monitoring"""
    client = SentimentAPIClient()
    
    start_time = datetime.now()
    try:
        result = client.predict(text)
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(
            f"Prediction successful",
            extra={
                'latency_ms': latency,
                'sentiment': result['sentiment'],
                'confidence': result['confidence']
            }
        )
        return result
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise
```

---

## Performance Optimization

### Batch vs. Single Requests

```python
# ❌ Inefficient: Multiple single requests
for text in texts:
    result = client.predict(text)  # 100 texts = 100 API calls

# ✅ Efficient: Single batch request
results = client.predict_batch(texts)  # 100 texts = 1 API call
```

### Connection Pooling

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class OptimizedClient:
    def __init__(self):
        self.session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
```

---

## Security Considerations

### 1. API Key Authentication (if implemented)

```python
class AuthenticatedClient:
    def __init__(self, api_key: str):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}'
        })
```

### 2. Input Sanitization

```python
def sanitize_input(text: str) -> str:
    """Clean input before sending"""
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > 5000:
        text = text[:5000]
    
    return text
```

---

## Support

For integration questions:
- Check API documentation: http://localhost:8000/docs
- Review example code in this guide
- Test with CLI tool: `./cli.py interactive`
