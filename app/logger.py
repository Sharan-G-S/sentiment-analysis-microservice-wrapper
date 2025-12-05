"""
Structured logging configuration
Logs inputs, outputs, latency, and errors
"""
import logging
import sys
import json
from datetime import datetime
from typing import Optional
from pathlib import Path


# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with JSON formatting
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler with standard formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler with JSON formatting
    json_handler = logging.FileHandler(LOGS_DIR / 'app.log')
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(console_handler)
    logger.addHandler(json_handler)
    
    return logger


# Prediction logger (separate file for predictions)
prediction_logger = logging.getLogger('predictions')
prediction_logger.setLevel(logging.INFO)

prediction_handler = logging.FileHandler(LOGS_DIR / 'predictions.log')
prediction_handler.setFormatter(JSONFormatter())
prediction_logger.addHandler(prediction_handler)


def log_prediction(
    request_id: str,
    input_text: str,
    prediction: str,
    confidence: float,
    latency_ms: float,
    success: bool,
    error: Optional[str] = None
):
    """
    Log prediction details in structured format
    
    Args:
        request_id: Request tracking ID
        input_text: Input text (truncated for logging)
        prediction: Predicted sentiment
        confidence: Prediction confidence
        latency_ms: Processing time in milliseconds
        success: Whether prediction succeeded
        error: Error message if failed
    """
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': request_id,
        'input_text': input_text[:200] + ('...' if len(input_text) > 200 else ''),
        'input_length': len(input_text),
        'prediction': prediction,
        'confidence': confidence,
        'latency_ms': latency_ms,
        'success': success
    }
    
    if error:
        log_data['error'] = error
    
    prediction_logger.info(json.dumps(log_data))


# Error logger
error_logger = logging.getLogger('errors')
error_logger.setLevel(logging.ERROR)

error_handler = logging.FileHandler(LOGS_DIR / 'errors.log')
error_handler.setFormatter(JSONFormatter())
error_logger.addHandler(error_handler)
