"""
FastAPI Production Wrapper for Sentiment Analysis Model
"""
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

# Load environment variables
load_dotenv()

from app.model import SentimentModel
from app.logger import get_logger, log_prediction
from app.metrics import MetricsCollector
from app.llm_enhancer import llm_enhancer, LLMProvider

# Initialize logger
logger = get_logger(__name__)
metrics = MetricsCollector()

# Model instance (loaded at startup)
model: Optional[SentimentModel] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for model loading/unloading"""
    global model
    logger.info("Starting application - Loading model...")
    try:
        model = SentimentModel()
        await model.load()
        logger.info("Model loaded successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise
    finally:
        logger.info("Shutting down application")
        if model:
            await model.unload()


# Initialize FastAPI app
app = FastAPI(
    title="Sentiment Analysis API",
    description="Production-ready sentiment analysis microservice using BERT",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class PredictionRequest(BaseModel):
    """Request schema for prediction endpoint"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    return_probabilities: bool = Field(False, description="Return class probabilities")
    request_id: Optional[str] = Field(None, description="Optional request tracking ID")
    enhanced: bool = Field(False, description="Use LLM enhancement for detailed analysis")
    llm_provider: Optional[str] = Field(None, description="LLM provider: 'groq', 'gemini', or 'auto'")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or only whitespace")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "text": "This product is amazing! I love it.",
                "return_probabilities": True,
                "request_id": "req_123"
            }
        }


class BatchPredictionRequest(BaseModel):
    """Request schema for batch prediction endpoint"""
    texts: List[str] = Field(..., min_items=1, max_items=100)
    return_probabilities: bool = Field(False)
    request_id: Optional[str] = Field(None)
    enhanced: bool = Field(False, description="Use LLM enhancement for batch insights")
    llm_provider: Optional[str] = Field(None, description="LLM provider: 'groq', 'gemini', or 'auto'")
    
    @validator('texts')
    def validate_texts(cls, v):
        cleaned = [text.strip() for text in v if text.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty text is required")
        return cleaned


class PredictionResponse(BaseModel):
    """Response schema for prediction"""
    sentiment: str = Field(..., description="Predicted sentiment (positive, negative, neutral)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    probabilities: Optional[Dict[str, float]] = Field(None, description="Class probabilities")
    latency_ms: float = Field(..., description="Processing time in milliseconds")
    request_id: Optional[str] = Field(None)
    timestamp: str = Field(..., description="Prediction timestamp")
    enhanced_analysis: Optional[Dict] = Field(None, description="LLM-powered detailed analysis")
    language_info: Optional[Dict] = Field(None, description="Language detection and translation")


class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions"""
    predictions: List[PredictionResponse]
    total_latency_ms: float
    request_id: Optional[str] = Field(None)
    batch_insights: Optional[Dict] = Field(None, description="Overall insights from batch analysis")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    version: str
    timestamp: str


class MetricsResponse(BaseModel):
    """Metrics response"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_latency_ms: float
    uptime_seconds: float
    model_info: Dict[str, str]


# API Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Sentiment Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/api/v1/predict",
            "batch_predict": "/api/v1/predict/batch",
            "health": "/health",
            "metrics": "/metrics"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns service health status and model availability
    """
    return HealthResponse(
        status="healthy" if model and model.is_loaded else "unhealthy",
        model_loaded=model.is_loaded if model else False,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """
    Get service metrics
    Returns request counts, latency stats, and model info
    """
    if not model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    stats = metrics.get_stats()
    return MetricsResponse(
        total_requests=stats['total_requests'],
        successful_requests=stats['successful_requests'],
        failed_requests=stats['failed_requests'],
        average_latency_ms=stats['average_latency_ms'],
        uptime_seconds=stats['uptime_seconds'],
        model_info=model.get_info()
    )


@app.post("/api/v1/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    """
    Predict sentiment for a single text
    
    - **text**: Input text to analyze (1-5000 characters)
    - **return_probabilities**: Whether to return class probabilities
    - **request_id**: Optional tracking ID
    - **enhanced**: Enable LLM-powered detailed analysis (explanation, key phrases, suggestions)
    - **llm_provider**: Choose LLM provider ('groq', 'gemini', or 'auto')
    """
    if not model or not model.is_loaded:
        logger.error("Prediction requested but model not loaded")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    start_time = time.time()
    
    try:
        # Log input
        logger.info(f"Prediction request received: {request.request_id or 'no_id'} (enhanced={request.enhanced})")
        
        # Detect language and translate if enhanced mode
        language_info = None
        text_to_analyze = request.text
        if request.enhanced:
            provider = LLMProvider(request.llm_provider) if request.llm_provider else LLMProvider.AUTO
            language_info = await llm_enhancer.detect_language_and_translate(request.text, provider)
            text_to_analyze = language_info.get('translated_text', request.text)
        
        # Run prediction
        result = await model.predict(
            text=text_to_analyze,
            return_probabilities=request.return_probabilities
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Get enhanced analysis if requested
        enhanced_analysis = None
        if request.enhanced:
            provider = LLMProvider(request.llm_provider) if request.llm_provider else LLMProvider.AUTO
            enhanced_analysis = await llm_enhancer.explain_sentiment(
                text=request.text,
                sentiment=result['sentiment'],
                confidence=result['confidence'],
                provider=provider
            )
        
        # Create response
        response = PredictionResponse(
            sentiment=result['sentiment'],
            confidence=result['confidence'],
            probabilities=result.get('probabilities'),
            latency_ms=round(latency_ms, 2),
            request_id=request.request_id,
            timestamp=datetime.utcnow().isoformat(),
            enhanced_analysis=enhanced_analysis,
            language_info=language_info
        )
        
        # Log prediction
        log_prediction(
            request_id=request.request_id or "unknown",
            input_text=request.text,
            prediction=result['sentiment'],
            confidence=result['confidence'],
            latency_ms=latency_ms,
            success=True
        )
        
        # Update metrics
        metrics.record_request(latency_ms, success=True)
        
        return response
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Prediction failed: {str(e)}", exc_info=True)
        
        # Log failed prediction
        log_prediction(
            request_id=request.request_id or "unknown",
            input_text=request.text,
            prediction="error",
            confidence=0.0,
            latency_ms=latency_ms,
            success=False,
            error=str(e)
        )
        
        # Update metrics
        metrics.record_request(latency_ms, success=False)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/api/v1/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict sentiment for multiple texts in batch
    
    - **texts**: List of texts to analyze (1-100 items)
    - **return_probabilities**: Whether to return class probabilities
    - **request_id**: Optional tracking ID
    - **enhanced**: Enable LLM-powered batch insights (trends, patterns, summary)
    - **llm_provider**: Choose LLM provider ('groq', 'gemini', or 'auto')
    """
    if not model or not model.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    start_time = time.time()
    predictions = []
    sentiments = []
    
    try:
        logger.info(f"Batch prediction request: {len(request.texts)} texts (enhanced={request.enhanced})")
        
        for idx, text in enumerate(request.texts):
            pred_start = time.time()
            result = await model.predict(text, request.return_probabilities)
            pred_latency = (time.time() - pred_start) * 1000
            
            predictions.append(PredictionResponse(
                sentiment=result['sentiment'],
                confidence=result['confidence'],
                probabilities=result.get('probabilities'),
                latency_ms=round(pred_latency, 2),
                request_id=f"{request.request_id or 'batch'}_{idx}",
                timestamp=datetime.utcnow().isoformat()
            ))
            sentiments.append(result['sentiment'])
        
        total_latency = (time.time() - start_time) * 1000
        
        # Get batch insights if enhanced mode
        batch_insights = None
        if request.enhanced:
            provider = LLMProvider(request.llm_provider) if request.llm_provider else LLMProvider.AUTO
            batch_insights = await llm_enhancer.analyze_batch_insights(
                texts=request.texts,
                sentiments=sentiments,
                provider=provider
            )
        
        metrics.record_request(total_latency, success=True)
        
        logger.info(f"Batch prediction completed: {len(predictions)} predictions in {total_latency:.2f}ms")
        
        return BatchPredictionResponse(
            predictions=predictions,
            total_latency_ms=round(total_latency, 2),
            request_id=request.request_id,
            batch_insights=batch_insights
        )
        
    except Exception as e:
        total_latency = (time.time() - start_time) * 1000
        logger.error(f"Batch prediction failed: {str(e)}", exc_info=True)
        metrics.record_request(total_latency, success=False)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
