"""
Sentiment Analysis Model - Synchronous Version for macOS
"""
import torch
from transformers import pipeline
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SentimentModel:
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model_name
        self.pipeline = None
        self.is_loaded = False
        try:
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
        except RuntimeError:
            # Already set, ignore error in tests
            pass
    
    async def load(self):
        """Load model"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            self._load_model()
            self.is_loaded = True
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def _load_model(self):
        """Load model synchronously"""
        self.pipeline = pipeline(
            "sentiment-analysis",
            model=self.model_name,
            device=-1
        )
    
    async def predict(self, text: str, return_probabilities: bool = False) -> Dict:
        """Make prediction synchronously"""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        # Run directly without executor
        results = self.pipeline(text, top_k=2)
        result = results[0]
        
        sentiment = "positive" if result['label'] == 'POSITIVE' else "negative"
        confidence = result['score']  # Keep as 0-1 range
        
        response = {
            "sentiment": sentiment,
            "confidence": round(confidence, 4)  # 0-1 range, not percentage
        }
        
        if return_probabilities:
            pos_score = confidence if sentiment == "positive" else (1 - confidence)
            response["probabilities"] = {
                "positive": round(pos_score, 4),
                "negative": round((1 - pos_score), 4)
            }
        
        return response
    
    async def unload(self):
        """Unload model"""
        self.pipeline = None
        self.is_loaded = False
    
    def get_info(self) -> Dict:
        """Get model info"""
        return {
            "model_name": self.model_name,
            "device": "cpu",
            "status": "loaded" if self.is_loaded else "not loaded",
            "framework": "PyTorch + Transformers"
        }
