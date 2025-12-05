"""
Example: Using the sentiment API client
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        """Predict sentiment for text"""
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


def main():
    """Example usage of the client"""
    client = SentimentAPIClient()
    
    print("=" * 60)
    print("Sentiment Analysis API - Example Usage")
    print("=" * 60)
    
    # 1. Health check
    print("\n1. Checking API health...")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Model loaded: {health['model_loaded']}")
    
    # 2. Single prediction
    print("\n2. Single prediction:")
    text = "This product is absolutely amazing! I love it!"
    result = client.predict(text, return_probabilities=True)
    print(f"   Text: {text}")
    print(f"   Sentiment: {result['sentiment']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Latency: {result['latency_ms']:.2f}ms")
    if result.get('probabilities'):
        print(f"   Probabilities:")
        for label, prob in result['probabilities'].items():
            print(f"     - {label}: {prob:.2%}")
    
    # 3. Batch prediction
    print("\n3. Batch prediction:")
    texts = [
        "Great service!",
        "Terrible experience",
        "It's okay, nothing special"
    ]
    batch_result = client.predict_batch(texts, return_probabilities=True)
    
    for i, pred in enumerate(batch_result['predictions']):
        print(f"\n   Text {i+1}: {texts[i]}")
        print(f"   Sentiment: {pred['sentiment']} ({pred['confidence']:.2%})")
    
    print(f"\n   Total latency: {batch_result['total_latency_ms']:.2f}ms")
    
    # 4. Different sentiments
    print("\n4. Testing various sentiments:")
    test_cases = [
        "I absolutely love this!",
        "This is the worst thing ever.",
        "It's decent, could be better.",
        "Exceeded my expectations!",
        "Very disappointed."
    ]
    
    for text in test_cases:
        result = client.predict(text)
        emoji = "😊" if result['sentiment'] == 'positive' else "😞"
        print(f"   {emoji} \"{text}\" → {result['sentiment']} ({result['confidence']:.2%})")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API.")
        print("   Make sure the API is running on http://localhost:8000")
        print("   Start it with: docker-compose up")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
