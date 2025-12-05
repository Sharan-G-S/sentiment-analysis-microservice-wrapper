"""
Unit tests for the sentiment analysis API
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_predict_positive_sentiment():
    """Test prediction with positive text"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict",
            json={
                "text": "This is amazing! I love it!",
                "return_probabilities": True
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "sentiment" in data
    assert "confidence" in data
    assert "latency_ms" in data
    assert "timestamp" in data
    assert data["sentiment"] in ["positive", "negative"]
    assert 0 <= data["confidence"] <= 1
    assert data["latency_ms"] > 0


@pytest.mark.asyncio
async def test_predict_negative_sentiment():
    """Test prediction with negative text"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict",
            json={
                "text": "This is terrible. I hate it!",
                "return_probabilities": False
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "sentiment" in data
    assert data["sentiment"] in ["positive", "negative"]


@pytest.mark.asyncio
async def test_predict_with_request_id():
    """Test prediction with custom request ID"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict",
            json={
                "text": "Good product",
                "request_id": "test_123"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "test_123"


@pytest.mark.asyncio
async def test_predict_empty_text():
    """Test prediction with empty text (should fail)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict",
            json={"text": ""}
        )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_predict_whitespace_only():
    """Test prediction with whitespace-only text (should fail)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict",
            json={"text": "   "}
        )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_predict_long_text():
    """Test prediction with very long text"""
    long_text = "This is great! " * 100
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict",
            json={"text": long_text}
        )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_batch_prediction():
    """Test batch prediction endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict/batch",
            json={
                "texts": [
                    "I love this!",
                    "This is terrible",
                    "It's okay, I guess"
                ],
                "return_probabilities": True
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "predictions" in data
    assert "total_latency_ms" in data
    assert len(data["predictions"]) == 3
    
    for pred in data["predictions"]:
        assert "sentiment" in pred
        assert "confidence" in pred
        assert "probabilities" in pred


@pytest.mark.asyncio
async def test_batch_prediction_empty_list():
    """Test batch prediction with empty list (should fail)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict/batch",
            json={"texts": []}
        )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test metrics endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Make a prediction first
        await client.post(
            "/api/v1/predict",
            json={"text": "Test text"}
        )
        
        # Get metrics
        response = await client.get("/metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_requests" in data
    assert "successful_requests" in data
    assert "failed_requests" in data
    assert "average_latency_ms" in data
    assert "uptime_seconds" in data
    assert "model_info" in data


@pytest.mark.asyncio
async def test_probabilities_sum_to_one():
    """Test that probabilities sum to approximately 1.0"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/predict",
            json={
                "text": "This is a test",
                "return_probabilities": True
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    if "probabilities" in data and data["probabilities"]:
        total = sum(data["probabilities"].values())
        assert abs(total - 1.0) < 0.01  # Allow small floating point error
