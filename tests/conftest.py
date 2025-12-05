"""
Test configuration
"""
import pytest
import asyncio
from unittest.mock import MagicMock


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_model(monkeypatch):
    """Mock the sentiment model to avoid loading heavy model in tests"""
    
    # Create a mock model instance
    mock_instance = MagicMock()
    mock_instance.is_loaded = True
    mock_instance.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    
    # Mock the predict method
    async def mock_predict(text, return_probabilities=False):
        # Simple rule-based mock for testing
        positive_words = ['amazing', 'love', 'great', 'excellent', 'wonderful', 'fantastic']
        negative_words = ['terrible', 'hate', 'awful', 'bad', 'worst', 'horrible']
        
        text_lower = text.lower()
        has_positive = any(word in text_lower for word in positive_words)
        has_negative = any(word in text_lower for word in negative_words)
        
        if has_positive and not has_negative:
            sentiment = "positive"
            confidence = 0.9999
            pos_prob = 0.9999
        elif has_negative and not has_positive:
            sentiment = "negative"
            confidence = 0.9999
            pos_prob = 0.0001
        else:
            sentiment = "positive"  # default
            confidence = 0.6
            pos_prob = 0.6
        
        result = {
            "sentiment": sentiment,
            "confidence": confidence
        }
        
        if return_probabilities:
            result["probabilities"] = {
                "positive": pos_prob,
                "negative": 1 - pos_prob
            }
        
        return result
    
    mock_instance.predict = mock_predict
    
    # Mock load method
    async def mock_load():
        mock_instance.is_loaded = True
    
    mock_instance.load = mock_load
    
    # Mock get_info method
    def mock_get_info():
        return {
            "model_name": "distilbert-base-uncased-finetuned-sst-2-english",
            "device": "cpu",
            "loaded": "true"  # String not bool for schema compatibility
        }
    
    mock_instance.get_info = mock_get_info
    
    # Patch the model instance in app.main
    from app import main
    monkeypatch.setattr(main, "model", mock_instance)
    
    return mock_instance

